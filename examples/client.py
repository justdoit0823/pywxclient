
"""A simple single thread WeChat client."""

import click
import sys
import time

from logging import config, getLogger

from pywxclient.core import Session, SyncClient, parse_message
from pywxclient.core.exception import (
    WaitScanQRCode, RequestError, APIResponseError, SessionExpiredError,
    AuthorizeTimeout, UnsupportedMessage)


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': (
                '[%(levelname)1.1s %(asctime)s %(process)d %(module)s:'
                '%(lineno)d] %(message)s')
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'filters': {
    },
    'handlers': {
        'console_log': {
            'level': 'DEBUG',
            'filters': [],
            'class': 'logging.StreamHandler',
            'stream': sys.stdout,
            'formatter': 'verbose'
        }
    },
    'loggers': {
        'client': {
            'handlers': ['console_log'],
            'level': 'DEBUG'
        },
        'pywxclient': {
            'handlers': ['console_log'],
            'level': 'DEBUG'
        }
    }
}


def sync_session(client):
    """Sync wechat session."""
    client_log = getLogger('client')
    authorize_url = client.open_authorize_url()

    client_log.info('Authorization url: {}'.format(authorize_url))

    while True:
        try:
            authorize_success = client.authorize()
        except WaitScanQRCode:
            continue
        except AuthorizeTimeout:
            client_log.warning('Waiting for authorization timeout.')
            sys.exit(0)

        if authorize_success:
            break

        client_log.info('Waiting for authorization...')
        time.sleep(2)

    client.login()
    client_log.info('Login success...')

    while True:
        try:
            sync_ret = client.sync_check()
            if sync_ret != 0:
                msgs = client.sync_message()
                for msg in msgs['AddMsgList']:
                    try:
                        msg_obj = parse_message(msg)
                    except UnsupportedMessage:
                        client_log.info('unsupported message %s', msg)
                        continue
                    else:
                        client_log.info(
                            'receive message %s, %s', msg_obj, msg_obj.message)

                client.flush_sync_key()
        except (RequestError, APIResponseError):
            client_log.info('api error.')
        except SessionExpiredError:
            client_log.warning('wechat session is expired....')
            break


@click.group()
def main():
    """Command entry."""
    pass


@main.command(name='run', help='start wechat client.')
def run():
    """Start wechat client."""
    config.dictConfig(LOGGING)
    client_log = getLogger('client')

    session = Session()
    client = SyncClient(session)
    sync_session(client)

    client_log.info('process down...')


if __name__ == '__main__':

    main()
