import singer

from tap_mws.streams.base import MWSBase

LOGGER = singer.get_logger()


class OrderItemsStream(MWSBase):
    STREAM_NAME = 'order_items'
    ID_FIELD = 'OrderItemId'
    KEY_PROPERTIES = [ID_FIELD]

    def initial_mws_api_call(self):
        LOGGER.info('MWS API call, list_order_items for %s', self.order_id)
        return self.connection.list_order_items(
            AmazonOrderId=self.order_id
        ).ListOrderItemsResult

    def next_mws_api_call(self, next_token):
        LOGGER.info('MWS API call, list_orders_by_next_token')
        return self.connection.list_orders_by_next_token(
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
        result = self._row_to_dict(row)
        result['OrderId'] = self.order_id
        return result
