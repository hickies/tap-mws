import singer

from tap_mws.streams.base import MWSBase


class OrderItemsStream(MWSBase):
    STREAM_NAME = 'order_items'
    ID_FIELD = 'OrderItemId'
    KEY_PROPERTIES = [ID_FIELD]

    def initial_mws_api_call(self):
        return self.connection.list_order_items(
            AmazonOrderId=self.order_id
        ).ListOrderItemsResult

    def next_mws_api_call(self, next_token):
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
