"""
The task runner
Implements the do_sync() and do_discover() actions
"""

import json
import sys

import singer
from boto.mws.connection import MWSConnection

from tap_mws.streams.orders import OrdersStream
from tap_mws.streams.order_items import OrderItemsStream

LOGGER = singer.get_logger()


class MWSRunner:
    """
    The task runner
    """
    def __init__(self, config, state, catalog):
        self.state = state
        self.config = config
        self._connection = None
        self.streams = {
            Stream: Stream(self.connection, config, state, catalog) for Stream in [OrdersStream, OrderItemsStream]
        }

    @property
    def connection(self):
        # Share the connection between the streams, but only establish it when we need it - lazy loading
        # Note: may be overkill
        if not self._connection:
            self._connection = MWSConnection(
                aws_access_key_id=self.config.get('aws_access_key'),
                aws_secret_access_key=self.config.get('client_secret'),
                Merchant=self.config.get('seller_id'),
                # mws_auth_token=self.config.get('mws_auth_token'),
            )
        return self._connection

    def do_discover(self):
        """
        Creates and outputs the catalog
        """
        LOGGER.info("Starting discovery.")

        catalog = [
            stream.generate_catalog()
            for stream in self.streams
        ]

        json.dump({'streams': catalog}, sys.stdout, indent=4)

    @staticmethod
    def sync_stream(stream):
        """
        Sync a single stream
        """
        try:
            stream.sync()
        except OSError as e:
            LOGGER.error(str(e))
            exit(e.errno)

        except Exception as e:
            LOGGER.error(str(e))
            LOGGER.error('Failed to sync endpoint {}, moving on!'
                         .format(stream.STREAM_NAME))
            raise e

    def do_sync(self):
        """
        Sync all streams
        """
        LOGGER.info("Starting sync.")

        # We need the list of product ids for the rankings report
        # so sync the products first
        order_stream = self.streams[OrdersStream]
        self.sync_stream(order_stream)

        order_items_stream = self.streams[OrderItemsStream]

        # TODO: Remove this - for testing only - get order items for all orders
        for order_id in order_stream.ids:
            order_items_stream.order_id = order_id
            self.sync_stream(order_items_stream)