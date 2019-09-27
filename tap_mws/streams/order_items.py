"""
The stream for order_items
"""

import singer

from tap_mws.streams.base import MWSBase

LOGGER = singer.get_logger()


class OrderItemsStream(MWSBase):
    """
    The stream of order items
    """
    STREAM_NAME = 'order_items'
    ID_FIELD = 'OrderItemId'
    KEY_PROPERTIES = [ID_FIELD]

    def __init__(self, *args, **kwargs):
        """
        Maybe a bit overkill - but pylint and pyCharm prefer it if
        any attribute used in a class is defined in __init__

        The order id gets set by the runner,
        just before the (base class's) sync method gets called
        """
        self.order_id = None
        super().__init__(*args, **kwargs)

    def initial_mws_api_call(self):
        """
        Call MWS's list_order_items and return the result
        """
        LOGGER.info('MWS API call, list_order_items for %s', self.order_id)
        return self.connection.list_order_items(
            AmazonOrderId=self.order_id
        ).ListOrderItemsResult

    def next_mws_api_call(self, next_token):
        """
        Call MWS's list_order_items_by_next_token and return the result
        """
        LOGGER.info('MWS API call, list_order_items_by_next_token')
        return self.connection.list_order_items_by_next_token(
            NextToken=next_token
        ).ListOrderItemsByNextTokenResult

    @staticmethod
    def get_list_from_api_result(result):
        return result.OrderItems.OrderItem

    # Actual limit: 30 initial requests, then 1 every 2 seconds
    @singer.ratelimit(29, 3)
    def check_rate_limit(self):
        pass

    def row_to_dict(self, row):
        """
        Add the order_id to the output stream
        """
        result = self._row_to_dict(row)
        result['OrderId'] = self.order_id
        return result
