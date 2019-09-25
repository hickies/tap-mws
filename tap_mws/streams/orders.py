import singer

from tap_mws.streams.base import MWSBase


class OrdersStream(MWSBase):
    STREAM_NAME = 'orders'
    ID_FIELD = 'SellerOrderId'
    KEY_PROPERTIES = [ID_FIELD]

    def initial_mws_api_call(self):
        arguments = dict(
            CreatedAfter=self.config.get('start_date'),
            MarketplaceId=[self.config.get('marketplace_id')],
        )
        order_status = self.config.get('order_status')
        if order_status is not None:
            arguments['OrderStatus'] = order_status
        return self.connection.list_orders(**arguments).ListOrdersResult

    def next_mws_api_call(self, next_token):
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
