
"""WeChat http request API module."""

import functools
import json
import math
import random
import time

from logging import getLogger

from pywxclient.core.exception import (
    APIResponseError, SessionExpiredError, LoginError)
from pywxclient.utils import ParseWxRes, json_dumps


__all__ = ['WeChatAPI']


_logger = getLogger(__name__)


def check_base_response(func):
    """Decorate for checking whether response is ok."""
    @functools.wraps(func)
    def wrapper(cls, *args, **kwargs):

        res = func(cls, *args, **kwargs)
        base_response = res.pop('BaseResponse', None)
        if base_response:
            retcode = base_response['Ret']
            if retcode != 0:
                _logger.debug('wechat api request failed res %s', res)
                if retcode == 1101:
                    raise SessionExpiredError

                raise APIResponseError

        return res

    return wrapper


def decode_json_response(res):
    """Decode wechat latin1 encoded json response."""
    return json.loads(res.text.encode('latin1').decode())


class WeChatAPI:
    """WeChat http api."""

    appid = 'wx782c26e4c19acffb'
    api_url_template = '{schema}://{endpoint}{url}'
    schema = 'https'
    wx_endpoints = ('wx.qq.com', 'wx2.qq.com')
    login_sub_host = 'login.'
    push_sub_host = 'webpush.'
    file_sub_host = 'file.'
    qrcode_uuid_url = '/jslogin'
    qrcode_url = '/qrcode'
    login_url = '/cgi-bin/mmwebwx-bin/login'
    init_url = '/cgi-bin/mmwebwx-bin/webwxinit'
    status_notify_url = '/cgi-bin/mmwebwx-bin/webwxstatusnotify'
    sync_check_url = '/cgi-bin/mmwebwx-bin/synccheck'
    do_sync_url = '/cgi-bin/mmwebwx-bin/webwxsync'
    contact_list_url = '/cgi-bin/mmwebwx-bin/webwxgetcontact'
    batch_contact_list_url = '/cgi-bin/mmwebwx-bin/webwxbatchgetcontact'
    upload_file_url = '/cgi-bin/mmwebwx-bin/webwxuploadmedia'
    msg_img_url = '/cgi-bin/mmwebwx-bin/webwxgetmsgimg'
    msg_voice_url = '/cgi-bin/mmwebwx-bin/webwxgetvoice'
    msg_media_url = '/cgi-bin/mmwebwx-bin/webwxgetmedia'
    sendmsg_url = '/cgi-bin/mmwebwx-bin/webwxsendmsg'
    sendmsg_img_url = '/cgi-bin/mmwebwx-bin/webwxsendmsgimg'
    sendmsg_gif_url = '/cgi-bin/mmwebwx-bin/webwxsendemoticon'
    sendmsg_video_url = '/cgi-bin/mmwebwx-bin/webwxsendvideomsg'
    sendmsg_app_url = '/cgi-bin/mmwebwx-bin/webwxsendappmsg'
    oplog_url = '/cgi-bin/mmwebwx-bin/webwxoplog'
    logout_url = '/cgi-bin/mmwebwx-bin/webwxlogout'

    low_timeout = (10, 15)
    middle_timeout = (15, 30)
    high_timeout = (30, 60)

    max_file_body = 512 * 1024  # 512k

    @classmethod
    def get_device_id(cls):
        """Generate a random device id."""
        return 'e' + str(random.randint(10 ** 14, 10 ** 15 - 1))

    @classmethod
    def get_base_request(cls, wx_session_data):
        """Construct base request."""
        wxuin = wx_session_data['wxuin']
        wxsid = wx_session_data['wxsid']
        skey = wx_session_data['skey']
        device_id = cls.get_device_id()
        base_request = {
            'Uin': wxuin, 'Sid': wxsid, 'Skey': skey, 'DeviceID': device_id}

        return base_request

    @classmethod
    def get_client_msg_id(cls):
        """Generate client message id."""
        return int(time.time() * 1000)

    @classmethod
    def get_wx_endpoint(cls):
        """Return wechat api endpoint."""
        return random.choice(cls.wx_endpoints)

    @classmethod
    def get_login_endpoint(cls, session):
        """Return wechat login related api endpoint."""
        return cls.login_sub_host + session.wx_endpoint

    @classmethod
    def get_push_endpoint(cls, session):
        """Return wechat push related api endpoint."""
        return cls.push_sub_host + session.wx_endpoint

    @classmethod
    def get_file_endpoint(cls, session):
        """Return wechat file related api endpoint."""
        return cls.file_sub_host + session.wx_endpoint

    @classmethod
    def get_qrcode_uuid(cls, session):
        """Get login qrcode uuid."""
        api_path = cls.api_url_template.format(
            schema=cls.schema, endpoint=cls.get_login_endpoint(session),
            url=cls.qrcode_uuid_url)
        params = {
            'appid': cls.appid, 'fun': 'new', '_': cls.get_client_msg_id()}
        res = session.get(api_path, params=params, timeout=cls.middle_timeout)

        data = ParseWxRes.parse_qrcode_uuid(res.content)

        return data['uuid']

    @classmethod
    def get_qrcode_url(cls, session, uuid):
        """Get authorize qrcode url."""
        return '{schema}://{endpoint}{url}/{uuid}'.format(
            schema=cls.schema, endpoint=cls.get_login_endpoint(session),
            url=cls.qrcode_url, uuid=uuid)

    @classmethod
    def get_login_info(cls, session, uuid):
        """Get login authorize info."""
        api_path = cls.api_url_template.format(
            schema=cls.schema, endpoint=cls.get_login_endpoint(session),
            url=cls.login_url)
        msg_id = cls.get_client_msg_id()
        params = {
            'loginicon': 'true', 'uuid': uuid, 'tip': 0,
            '_': msg_id, 'r': msg_id // 1992}
        res = session.get(api_path, params=params, timeout=cls.middle_timeout)
        _logger.debug('wechat login info res %s', res.content)
        data = ParseWxRes.parse_login(res.content)

        return data

    @classmethod
    def new_login_page(cls, session, login_api_path):
        """Create login page."""
        now_timestamp = int(time.time())
        params = {'scan': now_timestamp, 'version': 2, 'fun': 'new'}
        res = session.get(
            login_api_path, params=params, timeout=cls.middle_timeout)
        _logger.debug('wechat new login page res %s', res.content)
        data = ParseWxRes.parse_new_login_page(res.content)
        if data['ret'] != '0':
            raise LoginError(data['message'])

        return data

    @classmethod
    @check_base_response
    def wx_init(cls, session):
        """Initialize WeChat session."""
        api_path = cls.api_url_template.format(
            schema=cls.schema, endpoint=session.wx_endpoint, url=cls.init_url)
        wx_session_data = session.get_wx_session_data()
        headers = {'Content-Type': 'application/json; charset=utf-8'}
        params = {'pass_ticket': wx_session_data['pass_ticket']}

        data = {'BaseRequest': cls.get_base_request(wx_session_data)}

        res = session.post(
            api_path, params=params, data=json_dumps(
                data, compact=True, ensure_ascii=False).encode(),
            headers=headers, timeout=cls.high_timeout)

        return decode_json_response(res)

    @classmethod
    @check_base_response
    def notify_status(cls, session, user):
        """Notify session status."""
        api_path = cls.api_url_template.format(
            schema=cls.schema, endpoint=session.wx_endpoint,
            url=cls.status_notify_url)
        wx_session_data = session.get_wx_session_data()
        params = {'pass_ticket': wx_session_data['pass_ticket']}

        username = user['UserName']
        data = {'Code': 3, 'FromUserName': username, 'ToUserName': username}
        data['BaseRequest'] = cls.get_base_request(wx_session_data)
        data['ClientMsgId'] = cls.get_client_msg_id()

        res = session.post(
            api_path, params=params, data=json_dumps(
                data, compact=True, ensure_ascii=False).encode(),
            timeout=cls.middle_timeout)

        return decode_json_response(res)

    @classmethod
    def get_icon(cls, session, icon_url):
        """Get user wechat icon."""
        api_path = cls.api_url_template.format(
            schema=cls.schema, endpoint=session.wx_endpoint, url=icon_url)

        res = session.get(api_path, timeout=cls.middle_timeout)

        return res

    @classmethod
    def get_head_img(cls, session, headimg_url):
        """Get wechat head img."""
        api_path = cls.api_url_template.format(
            schema=cls.schema, endpoint=session.wx_endpoint,
            url=headimg_url)

        res = session.get(api_path, timeout=cls.middle_timeout)

        return res

    @classmethod
    def get_msg_img(cls, session, msg_id, original=True, stream=True):
        """Get message image."""
        api_path = cls.api_url_template.format(
            schema=cls.schema, endpoint=session.wx_endpoint,
            url=cls.msg_img_url)
        wx_session_data = session.get_wx_session_data()

        params = {'MsgID': msg_id, 'skey': wx_session_data['skey']}
        if not original:
            params['type'] = 'slave'

        res = session.get(
            api_path, params=params, timeout=cls.high_timeout, stream=stream)

        return res

    @classmethod
    def get_msg_voice(cls, session, msg_id, stream=True):
        """Get voice message data."""
        api_path = cls.api_url_template.format(
            schema=cls.schema, endpoint=session.wx_endpoint,
            url=cls.msg_voice_url)
        wx_session_data = session.get_wx_session_data()

        params = {'msgid': msg_id, 'skey': wx_session_data['skey']}

        res = session.get(
            api_path, params=params, timeout=cls.high_timeout, stream=stream)

        return res

    @classmethod
    def get_msg_media(
            cls, session, from_username, media_id, filename, stream=True):
        """Get message media data."""
        api_path = cls.api_url_template.format(
            schema=cls.schema, endpoint=cls.get_file_endpoint(session),
            url=cls.msg_media_url)
        wx_session_data = session.get_wx_session_data()
        session_cookies = session.get_session_cookies()

        wxuin = wx_session_data['wxuin']
        pass_ticket = wx_session_data['pass_ticket']
        webwx_data_ticket = session_cookies['webwx_data_ticket']
        params = {
            'sender': from_username, 'mediaid': media_id,
            'filename': filename, 'fromuser': wxuin,
            'pass_ticket': pass_ticket, 'webwx_data_ticket': webwx_data_ticket}

        res = session.get(
            api_path, params=params, timeout=cls.high_timeout, stream=stream)

        return res

    @classmethod
    @check_base_response
    def get_contact_list(cls, session):
        """Get user contact list."""
        api_path = cls.api_url_template.format(
            schema=cls.schema, endpoint=session.wx_endpoint,
            url=cls.contact_list_url)
        wx_session_data = session.get_wx_session_data()
        params = {
            'pass_ticket': wx_session_data['pass_ticket'],
            'r': cls.get_client_msg_id(), 'seq': 0,
            'skey': wx_session_data['skey']}

        res = session.get(api_path, params=params, timeout=cls.middle_timeout)

        return decode_json_response(res)

    @classmethod
    @check_base_response
    def mget_contact_list(cls, session, user_list):
        """Batch get user contact list."""
        api_path = cls.api_url_template.format(
            schema=cls.schema, endpoint=session.wx_endpoint,
            url=cls.batch_contact_list_url)
        wx_session_data = session.get_wx_session_data()
        headers = {'Content-Type': 'application/json; charset=utf-8'}
        params = {
            'pass_ticket': wx_session_data['pass_ticket'],
            'r': cls.get_client_msg_id(), 'type': 'ex'}

        base_request = cls.get_base_request(wx_session_data)
        data = {
            'BaseRequest': base_request, 'Count': len(user_list),
            'List': user_list}

        res = session.post(
            api_path, params=params, data=json_dumps(
                data, compact=True, ensure_ascii=False).encode(),
            headers=headers, timeout=cls.middle_timeout)

        return decode_json_response(res)

    @classmethod
    def check_sync(cls, session):
        """Check sync status."""
        api_path = cls.api_url_template.format(
            schema=cls.schema, endpoint=cls.get_push_endpoint(session),
            url=cls.sync_check_url)
        wx_session_data = session.get_wx_session_data()

        wxuin = wx_session_data['wxuin']
        wxsid = wx_session_data['wxsid']
        skey = wx_session_data['skey']
        sync_key = wx_session_data['sync_key']
        sync_key_str = '|'.join('_'.join(map(str, (
            k_pair['Key'], k_pair['Val']))) for k_pair in sync_key['List'])
        device_id = cls.get_device_id()
        params = {
            'uin': wxuin, 'sid': wxsid, 'skey': skey, 'deviceid': device_id,
            '_': cls.get_client_msg_id(), 'synckey': sync_key_str}

        res = session.get(api_path, params=params, timeout=cls.middle_timeout)
        _logger.debug('check wechat session sync res %s', res.content)
        data = ParseWxRes.parse_sync_check(res.content)

        if not data or data['retcode'] != '0':
            if data['retcode'] == '1101':
                raise SessionExpiredError

            raise APIResponseError

        return data

    @classmethod
    def upload_file(cls, session, file_obj, from_username, to_username):
        """Upload file to WeChat."""
        api_path = cls.api_url_template.format(
            schema=cls.schema, endpoint=cls.get_file_endpoint(session),
            url=cls.upload_file_url)
        wx_session_data = session.get_wx_session_data()
        session_cookies = session.get_session_cookies()

        params = {'f': 'json'}
        pass_ticket = wx_session_data['pass_ticket']
        base_request = cls.get_base_request(wx_session_data)
        data_len = file_obj.size
        data_media_type = file_obj.media_type()
        filename = file_obj.name

        upload_req = {
            'UploadType': 2, 'BaseRequest': base_request,
            'ClientMediaId': cls.get_client_msg_id(), 'TotalLen': data_len,
            'StartPos': 0, 'DataLen': data_len, 'MediaType': 4,
            'FromUserName': from_username, 'ToUserName': to_username,
            'FileMd5': file_obj.md5}

        def upload_chunk(chunk_index=0, chunk_num=1):
            data = {
                'id': 'WU_FILE_0', 'name': filename, 'type': data_media_type,
                'lastModifiedDate': file_obj.last_mtime, 'size': data_len,
                'mediatype': file_obj.short_type(),
                'uploadmediarequest': json_dumps(
                    upload_req, compact=True, ensure_ascii=False).encode(),
                'webwx_data_ticket': session_cookies['webwx_data_ticket'],
                'pass_ticket': pass_ticket}
            if chunk_num > 1:
                data['chunk'] = chunk_index
                data['chunks'] = chunk_num
                files = {'filename': (
                    filename, file_obj.read(cls.max_file_body),
                    data_media_type)}
            else:
                files = {'filename': (filename, file_obj, data_media_type)}

            res = session.post(
                api_path, params=params, data=data, files=files,
                timeout=cls.high_timeout)
            data = decode_json_response(res)

            return data

        chunks = math.ceil(data_len / cls.max_file_body)
        for chunk_idx in range(chunks):
            data = upload_chunk(chunk_idx, chunk_num=chunks)
            if chunk_idx < chunks - 1:
                if data['BaseResponse']['Ret'] != 0:
                    raise APIResponseError
            else:
                # The last uploaded chunk response
                if data['BaseResponse']['Ret'] != 0 or data[
                        'StartPos'] != data_len:
                    raise APIResponseError

                return data['MediaId']

    @classmethod
    @check_base_response
    def do_sync(cls, session):
        """Do WeChat session status sync."""
        api_path = cls.api_url_template.format(
            schema=cls.schema, endpoint=session.wx_endpoint,
            url=cls.do_sync_url)
        wx_session_data = session.get_wx_session_data()
        headers = {'Content-Type': 'application/json; charset=utf-8'}

        wxsid = wx_session_data['wxsid']
        skey = wx_session_data['skey']
        pass_ticket = wx_session_data['pass_ticket']
        params = {'sid': wxsid, 'pass_ticket': pass_ticket, 'skey': skey}

        base_request = cls.get_base_request(wx_session_data)
        sync_key = wx_session_data['sync_key']
        data = {'BaseRequest': base_request, 'SyncKey': sync_key}

        res = session.post(
            api_path, params=params, data=json_dumps(
                data, compact=True, ensure_ascii=False).encode(),
            headers=headers, timeout=cls.middle_timeout)

        return decode_json_response(res)

    @classmethod
    @check_base_response
    def send_text_message(cls, session, message):
        """Send text message api."""
        api_path = cls.api_url_template.format(
            schema=cls.schema, endpoint=session.wx_endpoint,
            url=cls.sendmsg_url)
        wx_session_data = session.get_wx_session_data()
        headers = {'Content-Type': 'application/json; charset=utf-8'}

        pass_ticket = wx_session_data['pass_ticket']
        params = {'pass_ticket': pass_ticket}

        base_request = cls.get_base_request(wx_session_data)
        msg_value = message.to_value()
        data = {'BaseRequest': base_request, 'Scene': 0, 'Msg': msg_value}

        res = session.post(
            api_path, params=params, data=json_dumps(
                data, compact=True, ensure_ascii=False).encode(),
            headers=headers, timeout=cls.low_timeout)

        return decode_json_response(res)

    @classmethod
    @check_base_response
    def send_image_message(cls, session, message):
        """Send image message api."""
        api_path = cls.api_url_template.format(
            schema=cls.schema, endpoint=session.wx_endpoint,
            url=cls.sendmsg_img_url)
        wx_session_data = session.get_wx_session_data()
        headers = {'Content-Type': 'application/json; charset=utf-8'}

        params = {'fun': 'async', 'f': 'json'}

        base_request = cls.get_base_request(wx_session_data)
        msg_value = message.to_value()
        data = {'BaseRequest': base_request, 'Scene': 0, 'Msg': msg_value}

        res = session.post(
            api_path, params=params, data=json_dumps(
                data, compact=True, ensure_ascii=False).encode(),
            headers=headers, timeout=cls.low_timeout)

        return decode_json_response(res)

    @classmethod
    @check_base_response
    def send_gif_message(cls, session, message):
        """Send gif message api."""
        api_path = cls.api_url_template.format(
            schema=cls.schema, endpoint=session.wx_endpoint,
            url=cls.sendmsg_gif_url)
        wx_session_data = session.get_wx_session_data()
        headers = {'Content-Type': 'application/json; charset=utf-8'}

        pass_ticket = wx_session_data['pass_ticket']
        params = {'pass_ticket': pass_ticket, 'fun': 'sys', 'f': 'json'}

        base_request = cls.get_base_request(wx_session_data)
        msg_value = message.to_value()
        msg_value['EmojiFlag'] = 2
        data = {'BaseRequest': base_request, 'Scene': 0, 'Msg': msg_value}

        res = session.post(
            api_path, params=params, data=json_dumps(
                data, compact=True, ensure_ascii=False).encode(),
            headers=headers, timeout=cls.low_timeout)

        return decode_json_response(res)

    @classmethod
    @check_base_response
    def send_video_message(cls, session, message):
        """Send video message api."""
        api_path = cls.api_url_template.format(
            schema=cls.schema, endpoint=session.wx_endpoint,
            url=cls.sendmsg_video_url)
        wx_session_data = session.get_wx_session_data()
        headers = {'Content-Type': 'application/json; charset=utf-8'}

        pass_ticket = wx_session_data['pass_ticket']
        params = {'pass_ticket': pass_ticket, 'fun': 'async', 'f': 'json'}

        base_request = cls.get_base_request(wx_session_data)
        msg_value = message.to_value()
        data = {'BaseRequest': base_request, 'Scene': 0, 'Msg': msg_value}

        res = session.post(
            api_path, params=params, data=json_dumps(
                data, compact=True, ensure_ascii=False).encode(),
            headers=headers, timeout=cls.low_timeout)

        return decode_json_response(res)

    @classmethod
    @check_base_response
    def send_file_message(cls, session, message):
        """Send file message api."""
        return cls.send_app_message(session, message)

    @classmethod
    @check_base_response
    def send_app_message(cls, session, message):
        """Send app message api."""
        api_path = cls.api_url_template.format(
            schema=cls.schema, endpoint=session.wx_endpoint,
            url=cls.sendmsg_app_url)
        wx_session_data = session.get_wx_session_data()
        headers = {'Content-Type': 'application/json; charset=utf-8'}

        pass_ticket = wx_session_data['pass_ticket']
        params = {'pass_ticket': pass_ticket, 'fun': 'async', 'f': 'json'}

        base_request = cls.get_base_request(wx_session_data)
        msg_value = message.to_value()
        data = {'BaseRequest': base_request, 'Scene': 0, 'Msg': msg_value}

        res = session.post(
            api_path, params=params, data=json_dumps(
                data, compact=True, ensure_ascii=False).encode(),
            headers=headers, timeout=cls.low_timeout)

        return decode_json_response(res)

    @classmethod
    @check_base_response
    def set_user_remark(cls, session, username, remark):
        """Set user remark api."""
        api_path = cls.api_url_template.format(
            schema=cls.schema, endpoint=session.wx_endpoint, url=cls.oplog_url)
        wx_session_data = session.get_wx_session_data()
        headers = {'Content-Type': 'application/json; charset=utf-8'}

        pass_ticket = wx_session_data['pass_ticket']
        params = {'pass_ticket': pass_ticket}

        base_request = cls.get_base_request(wx_session_data)
        data = {
            'BaseRequest': base_request, 'UserName': username,
            'RemarkName': remark, 'CmdId': 2}

        res = session.post(
            api_path, params=params, data=json_dumps(
                data, compact=True, ensure_ascii=False).encode(),
            headers=headers, timeout=cls.low_timeout)

        return decode_json_response(res)

    @classmethod
    @check_base_response
    def logout(cls, session):
        """Logout wechat session."""
        api_path = cls.api_url_template.format(
            schema=cls.schema, endpoint=session.wx_endpoint,
            url=cls.logout_url)
        wx_session_data = session.get_wx_session_data()

        wxsid = wx_session_data['wxsid']
        wxuin = wx_session_data['wxuin']
        skey = wx_session_data['skey']
        params = {'skey': skey, 'type': 1, 'redirect': 0}

        data = {'sid': wxsid, 'uin': wxuin}

        res = session.post(
            api_path, params=params, data=data, timeout=cls.low_timeout)

        return decode_json_response(res)
