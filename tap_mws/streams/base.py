"""
Stream base class
"""
import inspect
import os

import singer


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

    def __init__(self, connection, config, state, catalog):
        self.connection = connection
        self.config = config
        self.state = state
        self.ids = None
        # self.catalog = catalog

        self.schema = None

        if catalog:
            stream_details = stream_details_from_catalog(catalog, self.STREAM_NAME)
            if stream_details:
                self.schema = stream_details.schema.to_dict()['properties']
                self.key_properties = stream_details.key_properties

        if not self.schema:
            self.schema = singer.utils.load_json(
                os.path.normpath(
                    os.path.join(
                        self.get_class_path(),
                        '../schemas/{}.json'.format(self.STREAM_NAME))))
            self.key_properties = self.KEY_PROPERTIES

        # self.state = state
        # bookmark_date = singer.bookmarks.get_bookmark(
        #     state=state,
        #     tap_stream_id=self.STREAM_NAME,
        #     key='last_record'
        # )
        # if not bookmark_date:
        #     bookmark_date = client.start_date
        #
        # self.bookmark_date = str_to_date(bookmark_date)
        #
        # self.product_ids = []

    def row_to_dict(self, row):
        result = row.__dict__
        del result['_connection']
        for key, value in result.items():
            if hasattr(value, '_connection'):
                result[key] = self.row_to_dict(value)
        return result

    def sync(self):
        """
        Perform sync action
        These steps are the same for all streams
        Differences between streams are implemented by overriding .do_sync() method
        """
        singer.write_schema(self.STREAM_NAME, self.schema, self.key_properties)
        rows = self.request_list()
        self.ids = []
        with singer.metrics.Counter('record_count', {'endpoint': self.STREAM_NAME}) as counter:
            for row in rows:
                row_as_dict = self.row_to_dict(row)
                message = singer.RecordMessage(
                    stream=self.STREAM_NAME,
                    record=row_as_dict,
                )
                singer.write_message(message)
                self.ids.append(row_as_dict[self.ID_FIELD])
            counter.increment()
        # singer.write_state(self.state)


    # def do_sync(self):
    #     """
    #     Main sync functionality
    #     Most of the streams use this
    #     A few of the streams work differently and override this method
    #     """
    #     try:
    #         response = self.client.make_request(self.URI.format(self.bookmark_date.strftime('%Y-%m-%d')))
    #     except RequestError:
    #         return
    #
    #     new_bookmark_date = self.bookmark_date
    #
    #     with singer.metrics.Counter('record_count', {'endpoint': self.STREAM_NAME}) as counter:
    #         for entry in self.traverse_nested_dicts(response.json(), self.RESPONSE_LEVELS):
    #             record = self.RECORD_CLASS(entry, self.schema)
    #             new_bookmark_date = max(new_bookmark_date, record.bookmark)
    #             singer.write_message(singer.RecordMessage(
    #                 stream=self.STREAM_NAME,
    #                 record=record.for_export,
    #             ))
    #         counter.increment()
    #
    #     self.state = singer.write_bookmark(self.state, self.STREAM_NAME, 'last_record', date_to_str(new_bookmark_date))
    def check_rate_limit(self):
        raise NotImplemented

    def request_list(self):
        # TODO: Rate limiting, error handling
        self.check_rate_limit()
        result = self.initial_mws_api_call()

        done = False
        while not done:
            for order_item in self.get_list_from_api_result(result):
                yield order_item

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
