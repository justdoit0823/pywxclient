
"""A multiple threads WeChat client."""

import click
import queue
import sys
import threading
import time

from logging import config, getLogger

from pywxclient.core import Session, SyncClient, TextMessage, parse_message
from pywxclient.core.exception import (
    WaitScanQRCode, RequestError, APIResponseError, SessionExpiredError,
    UnsupportedMessage)


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
            'class': 'logging.FileHandler',
            'filename': 'wechat_client.log',
            'formatter': 'verbose'
        }
    },
    'loggers': {
        'client': {
            'handlers': ['console_log'],
            'level': 'DEBUG'
        }
    }
}


_client_contacts = {}


def build_contact(client):
    """Get user WeChat contact."""
    contacts = client.get_contact()
    for user in contacts:
        _client_contacts[user['UserName']] = user

    _client_contacts[client.user['UserName']] = client.user


def get_user(username):
    """Return user info identified by username."""
    return _client_contacts.get(username, {})


def sync_session(client, input_queue, login_event, exit_event):
    """Sync wechat session."""
    client_log = getLogger('client')
    authorize_url = client.open_authorize_url()

    authorization_prompt = 'Authorization url: {}'.format(authorize_url)
    client_log.info(authorization_prompt)

    while True:
        try:
            authorize_success = client.authorize()
        except WaitScanQRCode:
            continue

        if authorize_success:
            break

        client_log.info('Waiting for authorize...')
        time.sleep(2)

    client.login()
    build_contact(client)
    client_log.debug('Login success...')
    login_event.set()

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
                        if msg_obj.message:
                            input_queue.put(msg_obj)

                client.flush_sync_key()
        except (RequestError, APIResponseError):
            client_log.info('api error.')
        except SessionExpiredError:
            client_log.error('wechat session is expired....')
            exit_event.set()
            break
        except Exception:
            continue


def show_input_message(client, input_queue, msg_queue, exit_event):
    """Show input message thread."""
    while not exit_event.is_set():
        try:
            msg_obj = input_queue.get(timeout=5)
        except queue.Empty:
            continue
        else:
            from_user = msg_obj.from_user
            user_info = get_user(from_user)
            show_username = user_info['RemarkName'] or user_info[
                'NickName'] if user_info else from_user
            print('{0}: {1}'.format(show_username, msg_obj.message))
            if from_user == client.user['UserName']:
                print('continue:', end=' ', flush=True)
                reply_msg = sys.stdin.readline()
                if reply_msg and reply_msg != '\n':
                    msg_queue.put((reply_msg, msg_obj.to_user))
            else:
                print('reply:', end=' ', flush=True)
                reply_msg = sys.stdin.readline()
                if reply_msg and reply_msg != '\n':
                    msg_queue.put((reply_msg, from_user))


def reply_message(client, msg_queue, login_event, exit_event):
    """Reply message to wechat."""
    client_log = getLogger('client')

    login_event.wait()
    client_log.info('start sending message.')

    while not exit_event.is_set():
        try:
            msg_content, to_user = msg_queue.get(timeout=3)
        except queue.Empty:
            continue

        try:
            msg = TextMessage(
                client.user['UserName'], to_user, msg_content)
            client.send_message(msg)
        except (RequestError, APIResponseError):
            client_log.info('api error.')
        except SessionExpiredError:
            client_log.error('wechat session is expired....')
            break


@click.group()
def main():
    """Command entry."""
    pass


@main.command(name='run', help='start wechat client.')
def run(**kwargs):
    """Start wechat client."""
    input_queue = queue.Queue()
    msg_queue = queue.Queue()
    login_event = threading.Event()
    exit_event = threading.Event()

    config.dictConfig(LOGGING)
    client_log = getLogger('client')

    session = Session()
    client = SyncClient(session)
    session_thread = threading.Thread(
        target=sync_session,
        args=(client, input_queue, login_event, exit_event))
    reply_thread = threading.Thread(
        target=reply_message,
        args=(client, msg_queue, login_event, exit_event))

    session_thread.start()
    reply_thread.start()

    show_input_message(client, input_queue, msg_queue, exit_event)

    session_thread.join()
    reply_thread.join()

    client_log.info('process down...')


if __name__ == '__main__':

    main()
