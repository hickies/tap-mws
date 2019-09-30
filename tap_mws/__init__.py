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
    args = singer.utils.parse_args(
        required_config_keys=['seller_id', 'aws_access_key',
                              'client_secret', 'marketplace_id', 'start_date', 'user_agent']
    )

    # When writing out the bookmark/state, it adds an extra 'level' to the
    # data - the toplevel now being 'value', with 'bookmarks' its one and only attribute
    # When using the state (extracting or updating a bookmark), it expects 'bookmarks'
    # to be at the root
    # So when reading the state back in, remove the 'value' at the top
    # so 'bookmarks' is back at the top
    # I don't know why it works like this, or what I'm missing here
    state = args.state
    if state:
        state = state['value']

    runner = MWSRunner(
        config=args.config,
        state=state,
        catalog=args.catalog
    )

    if args.discover:
        runner.do_discover()
    else:
        runner.do_sync()


if __name__ == '__main__':
    main()
