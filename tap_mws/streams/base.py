"""
Stream base class
"""
import inspect
import os

import singer

LOGGER = singer.get_logger()


def stream_details_from_catalog(catalog, stream_name):
    """
    Extract details for a single stream from the catalog
    """
    for stream_details in catalog.streams:
        if stream_details.tap_stream_id == stream_name:
            return stream_details
    return None


class MWSBase:
    """
    Stream base class
    """
    ID_FIELD = ''
    STREAM_NAME = ''
    KEY_PROPERTIES = []
    BOOKMARK_FIELD = None
    KEEP_IDS = False
    BATCH_SIZE = None

    def __init__(self, connection, config, state, catalog):
        self.connection = connection
        self.config = config
        self.state = state
        self.ids = None
        self.bookmark_date = None
        self.catalog = catalog
        self.include_stream = True  # Should this stream be sync'd
        self.exclude_fields = []  # A list of fields to exclude from the output stream
        self.schema = None

        if catalog:
            stream_details = stream_details_from_catalog(catalog, self.STREAM_NAME)
            if stream_details:
                self.schema = stream_details.schema.to_dict()['properties']
                self.key_properties = stream_details.key_properties
                self.include_stream = self.include_stream_from_metadata(stream_details.metadata)
                self.exclude_fields = self.exclude_fields_from_metadata(stream_details.metadata)

        # Schema not loaded from the catalog, get it from the json file instead
        if not self.schema:
            self.schema = singer.utils.load_json(
                os.path.normpath(
                    os.path.join(
                        self.get_class_path(),
                        '../schemas/{}.json'.format(self.STREAM_NAME))))
            self.key_properties = self.KEY_PROPERTIES

    @staticmethod
    def include_stream_from_metadata(metadata):
        """
        Should this stream be sync'd - as described in the meta data

        There are two different formats
        1. As found in the documentation
        https://github.com/singer-io/getting-started/blob/master/docs/SYNC_MODE.md#streamfield-selection
        "metadata": [
        {
          "breadcrumb": [],
          "metadata": {
            "selected": "false"
          }
        }]

        2. As found in the catalog.json file created during --discovery
            "metadata": {
                "selected": true,
                "is_view": false,
                "schema-name": "orders"
            },

        Both formats are handled here
        """

        # Format 1
        if isinstance(metadata, dict):
            return metadata.get('selected')

        # Format 2
        for item in metadata:
            if item.get('breadcrumb') == []:
                if item.get('metadata') and item['metadata'].get('selected') == 'false':
                    return False
        return True

    @staticmethod
    def exclude_fields_from_metadata(metadata):
        """
        Create a list of any fields which should be excluded from the export,
        as per the metadata. See
        https://github.com/singer-io/getting-started/blob/master/docs/SYNC_MODE.md#streamfield-selection

        Example:
        "metadata": [
            {
              "breadcrumb": [],
              "metadata": {
                "selected": "true"
              }
            },{
              "breadcrumb": [
                "properties",
                "SellerSKU"
              ],
              "metadata": {
                "inclusion": "unsupported",
                "selected": "true"
              }
            }
        ]
        This includes the (order items) stream, but excludes the stream's SellerSKU field
        from the exported data
        """
        if isinstance(metadata, dict):
            return []
        result = []
        for item in metadata:
            # No breadcrumb specified, i.e. no field specified. Skip this
            if item.get('breadcrumb') in [None, []]:
                continue

            # For meaning of inclusion and selected see
            # https://github.com/singer-io/getting-started/blob/master/docs/SYNC_MODE.md#streamfield-selection
            inclusion = item['metadata']['inclusion']
            selected = item['metadata']['selected']

            if not singer.utils.should_sync_field(inclusion, selected):
                breadcrumb = item['breadcrumb']
                assert breadcrumb[0] == 'properties'
                result.append(breadcrumb[1:])

        return result

    def _row_to_dict(self, row):
        """
        A recursive process to transform the attribute-based row to a dictionary

        For instance row.id becomes result['id']
        """
        result = row.__dict__

        # Don't export the connection
        del result['_connection']

        for key, value in result.items():
            if hasattr(value, '_connection'):
                # The row may be nested
                result[key] = self._row_to_dict(value)
        return result

    def row_to_dict(self, row):
        """
        Hook for subclasses to perform some additional processing
        """
        return self._row_to_dict(row)

    def starting_bookmark_date(self):
        """
        Get the start date, either from the state or from the config
        """
        if self.BOOKMARK_FIELD is None:
            return None

        bookmark_date = singer.bookmarks.get_bookmark(
            state=self.state,
            tap_stream_id=self.STREAM_NAME,
            key=self.BOOKMARK_FIELD
        )
        if not bookmark_date:
            bookmark_date = self.config.get('start_date')

        return bookmark_date

    @staticmethod
    def remove_one_excluded_field(path, row):
        """
        Remove field <path> from the row - if it exists
        """
        remove_from = row
        for part in path[:-1]:
            if not remove_from or part not in remove_from:
                # Field not in the returned data
                return
            remove_from = remove_from[part]

        if not remove_from or path[-1] not in remove_from:
            return
        del remove_from[path[-1]]

    def remove_excluded_fields(self, row):
        """
        Remove all excluded fields from the row
        """
        if not self.exclude_fields:
            return

        for path in self.exclude_fields:
            if not path:
                continue

            self.remove_one_excluded_field(path, row)

    def sync(self):
        """
        Perform sync action
        These steps are the same for all streams
        Differences between streams are implemented by overriding .do_sync() method
        """
        if not self.KEEP_IDS and not self.include_stream:
            LOGGER.info('Skipping stream %s - excluded in catalog', self.STREAM_NAME)
            return

        new_bookmark_date = self.bookmark_date = self.starting_bookmark_date()

        # Will be set to false if we stop early due to reaching the end of a batch
        # to tell the runner to continue with the next batch
        all_done = True

        singer.write_schema(self.STREAM_NAME, self.schema, self.key_properties)
        rows = self.request_list()
        self.ids = []
        with singer.metrics.Counter('record_count', {'endpoint': self.STREAM_NAME}) as counter:
            for row in rows:
                row_as_dict = self.row_to_dict(row)
                if self.KEEP_IDS:
                    self.ids.append(row_as_dict[self.ID_FIELD])
                self.remove_excluded_fields(row_as_dict)
                message = singer.RecordMessage(
                    stream=self.STREAM_NAME,
                    record=row_as_dict,
                    time_extracted=singer.utils.now()
                )
                if self.include_stream:
                    singer.write_message(message)
                if self.BOOKMARK_FIELD:
                    new_bookmark_date = max(new_bookmark_date, row_as_dict[self.BOOKMARK_FIELD])
                counter.increment()

                # Stop if we've done enough for one batch
                if self.BATCH_SIZE and counter.value >= self.BATCH_SIZE:
                    # Sync action stopped due to end of batch - so probably more rows
                    # Note that there is a 1/BATCH_SIZE chance that the end of a
                    # batch is exactly the end of the whole process. In that case
                    # the runner will make one more .sync request, for one more (empty) batch
                    all_done = False
                    break

        if self.BOOKMARK_FIELD:
            singer.write_bookmark(
                self.state, self.STREAM_NAME, self.BOOKMARK_FIELD, new_bookmark_date
            )

        return all_done

    def check_rate_limit(self):
        """
        Empty function - a place for subclasses to decorate
        with singer's rate limiting decorator
        """
        raise NotImplementedError

    def initial_mws_api_call(self):
        """
        Request the first page of rows from MWS
        """
        raise NotImplementedError

    @staticmethod
    def get_list_from_api_result(result):
        """
        The order and order_items boto/API calls both return a list of rows
        The exact path from the response to these lists vary
        This function takes the response and returns the list
        """
        raise NotImplementedError

    def next_mws_api_call(self, next_token):
        """
        Request the next page of rows from MWS
        """
        raise NotImplementedError

    def request_list(self):
        """
        An iterator function which returns all the rows
        spanning multiple pages if necessary

        Calls are rate limited, using singer's rate limiting function
        This may be overkill, as the boto library also seems to be rate limiting
        """
        self.check_rate_limit()
        result = self.initial_mws_api_call()

        done = False
        while not done:
            for row in self.get_list_from_api_result(result):
                yield row

            if hasattr(result, 'NextToken'):
                self.check_rate_limit()
                result = self.next_mws_api_call(result.NextToken)
            else:
                done = True

    def get_class_path(self):
        """
        The absolute path of the source file for this class
        """
        return os.path.dirname(inspect.getfile(self.__class__))

    def generate_catalog(self):
        """
        Builds the catalog entry for this stream
        """
        return dict(
            tap_stream_id=self.STREAM_NAME,
            stream=self.STREAM_NAME,
            key_properties=self.key_properties,
            schema=self.schema,
            metadata={
                'selected': True,
                'schema-name': self.STREAM_NAME,
                'is_view': False,
            }
        )
