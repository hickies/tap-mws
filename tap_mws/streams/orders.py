"""
The stream for orders
"""

import singer

from tap_mws.streams.base import MWSBase

LOGGER = singer.get_logger()


class OrdersStream(MWSBase):
    """
    The stream of orders
    """
    STREAM_NAME = 'orders'
    BOOKMARK_FIELD = 'CreatedAfter'
    ID_FIELD = 'AmazonOrderId'
    KEY_PROPERTIES = [ID_FIELD]
    KEEP_IDS = True
    BATCH_SIZE = 100

    def initial_mws_api_call(self):
        """
        Call MWS's list_orders and return the result
        """
        LOGGER.info('MWS API call, list_orders from %s', self.bookmark_date)
        arguments = dict(
            CreatedAfter=self.bookmark_date,
            MarketplaceId=[self.config.get('marketplace_id')],
        )
        order_status = self.config.get('order_status')
        if order_status is not None:
            arguments['OrderStatus'] = [o.strip() for o in order_status.split(',')]
        return self.connection.list_orders(**arguments).ListOrdersResult

    def next_mws_api_call(self, next_token):
        """
        Call MWS's list_orders_by_next_token and return the result
        """
        LOGGER.info('MWS API call, list_orders_by_next_token')
        return self.connection.list_orders_by_next_token(
            NextToken=next_token
        ).ListOrdersByNextTokenResult

    @staticmethod
    def get_list_from_api_result(result):
        return result.Orders.Order

    # Actual limit: 6 initial requests, then 1 every 60 seconds. Err on the side of caution
    @singer.ratelimit(5, 65)
    def check_rate_limit(self):
        pass
