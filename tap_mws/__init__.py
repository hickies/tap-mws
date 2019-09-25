"""
tap-mws package

Singer tap for the Amazon MWS API
Singer: https://github.com/singer-io/getting-started
Amazon MWS API: http://docs.developer.amazonservices.com/en_US/dev_guide/index.html
"""

import singer

import tap_mws.streams
from tap_mws.runner import MWSRunner

LOGGER = singer.get_logger()


@singer.utils.handle_top_exception(LOGGER)
def main():
    """
    Main function - process args, build runner, execute request
    """
    # TODO: Optional argument 'order status' - check for this?
    args = singer.utils.parse_args(
        required_config_keys=['seller_id', 'aws_access_key',
                              'client_secret', 'marketplace_id', 'start_date', 'user_agent']
    )

    runner = MWSRunner(
        config=args.config,
        state=args.state,
        catalog=args.catalog
    )

    if args.discover:
        runner.do_discover()
    else:
        runner.do_sync()


if __name__ == '__main__':
    main()
