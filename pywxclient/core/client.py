
"""WeChat Client module."""

from urllib.parse import urlparse
import webbrowser

from pywxclient.core.api import WeChatAPI
from pywxclient.core.exception import (
    AuthorizeTimeout, UnknownWindowCode, WaitScanQRCode,
    MessageAlreadyAcknowledge, UnacknowledgedMessage, UnsupportedMessage)
from pywxclient.core.message import (
    TextMessage, ImageMessage, GifImageMessage, VideoMessage, FileMessage,
    VoiceMessage)
from pywxclient.core.session import Session


__all__ = ['Client', 'SyncClient']


class Client:
    """WeChat client base class."""

    ok_login_code = (200, 201, 400, 408)

    def __init__(self, session, api_cls=WeChatAPI):
        """Initialize client with Session object and api class."""
        self.session = session
        self.user = None
        self.userAvatar = None
        self._uuid = None
        self._login_uri = None
        self._api_cls = api_cls

    def dump(self):
        """Dump client object as dict."""
        return {
            'session': self.session.dump(), 'user': self.user,
            'uuid': self._uuid}

    @classmethod
    def load(cls, client_dict):
        """Restore client from dict."""
        session = Session(session_data=client_dict['session'])
        client = cls(session)
        client.user = client_dict['user']
        client._uuid = client_dict['uuid']
        return client

    def get_authorize_url(self):
        """Get WeChat authorize url."""
        raise NotImplementedError

    def authorize(self):
        """Request WeChat authorize."""
        raise NotImplementedError

    def login(self):
        """Login in WeChat."""
        raise NotImplementedError

    def get_contact(self):
        """Get WeChat contacts."""
        raise NotImplementedError

    def get_batch_contact(self, user_list):
        """Batch getting WeChat contacts.

        :param user_list: a list contains dict like {
            'UserName': 'username', 'EncryChatRoomId': ''}.
        """
        raise NotImplementedError

    def sync_check(self):
        """Check WeChat sync status."""
        raise NotImplementedError

    def sync_message(self):
        """Sync WeChat message."""
        raise NotImplementedError

    def upload(self, file_obj, to_username):
        """Upload message resource to WeChat."""
        raise NotImplementedError

    def send_message(self, message):
        """Send WeChat message."""
        raise NotImplementedError

    def flush_sync_key(self):
        """Update WeChat session sync key.

        This must be invoked after successfully handling new messages.
        Otherwise client is at risk of losing messages.
        """
        self.session.sync(self._sync_key)

    def logout(self):
        """Logout WeChat."""
        raise NotImplementedError

    def close(self):
        """Close client."""
        self.session.close()
        self.session = None
        self.userAvatar = None
        self._uuid = None
        self._login_uri = None
        self.user = None
        self._sync_key = None


class SyncClient(Client):
    """Sync request WeChat client."""

    msg_send_routines = {
        TextMessage.msg_type: WeChatAPI.send_text_message,
        ImageMessage.msg_type: WeChatAPI.send_image_message,
        GifImageMessage.msg_type: WeChatAPI.send_gif_message,
        VideoMessage.msg_type: WeChatAPI.send_video_message,
        FileMessage.msg_type: WeChatAPI.send_file_message
    }

    def get_authorize_url(self):
        """Get WeChat authorize url."""
        uuid = self._api_cls.get_qrcode_uuid(self.session)
        self._uuid = uuid
        return self._api_cls.get_qrcode_url(self.session, uuid)

    def open_authorize_url(self):
        """Open WeChat authorization url in system-default browser."""
        authorize_url = self.get_authorize_url()
        webbrowser.open(authorize_url)
        return authorize_url    # allow for url passthrough

    def authorize(self):
        """Start wechat authorization."""
        if self.session.authorized:
            return True

        login_info = self._api_cls.get_login_info(self.session, self._uuid)
        login_code = int(login_info['code'])

        if login_code not in self.ok_login_code:
            raise UnknownWindowCode

        if login_code == 408:
            # waiting scan qrcode
            raise WaitScanQRCode
        elif login_code == 400:
            # authorize timeout
            raise AuthorizeTimeout
        elif login_code == 201:
            # waiting authorize confirm
            self.userAvatar = login_info['userAvatar']
            return False

        self._login_uri = login_info['redirect_uri']
        endpoint = urlparse(self._login_uri).netloc
        self.session.finish_authorize(endpoint)
        return True

    def login(self):
        """Login wechat session."""
        if self.session.is_active():
            # already login
            return

        page_info = self._api_cls.new_login_page(self.session, self._login_uri)
        self.session.initialize_wx_session(page_info)

        init_res = self._api_cls.wx_init(self.session)
        self.user = init_res['User']

        self.session.sync(init_res['SyncKey'])

    def get_contact(self):
        """Get wechat contact."""
        contact_res = self._api_cls.get_contact_list(self.session)
        return contact_res['MemberList']

    def get_batch_contact(self, user_list):
        """Batch getting contact."""
        contact_res = self._api_cls.mget_contact_list(self.session, user_list)
        return contact_res['ContactList']

    def get_icon(self, icon_url):
        """Get user icon.

        :param icon_url: icon url.
        """
        return self._api_cls.get_icon(self.session, icon_url)

    def get_head_img(self, headimg_url):
        """Get user head image.

        :param headimg_url: headimg url.
        """
        return self._api_cls.get_head_img(self.session, headimg_url)

    def sync_check(self):
        """Check session status."""
        check_res = self._api_cls.check_sync(self.session)
        return int(check_res['selector'])

    def sync_message(self):
        """Sync wechat message."""
        message = self._api_cls.do_sync(self.session)

        sync_key = message['SyncKey']
        self._sync_key = sync_key

        return message

    def upload(self, file_obj, to_username):
        """Upload resource to WeChat."""
        return self._api_cls.upload_file(
            self.session, file_obj, self.user['UserName'], to_username)

    def send_message(self, message):
        """Send message to WeChat."""
        if message.check_ack_status():
            raise MessageAlreadyAcknowledge

        msg_ret = self.msg_send_routines[message.msg_type](
            self.session, message)

        local_msg_id = msg_ret['LocalID']
        msg_id = msg_ret['MsgID']
        message.ack(local_msg_id, msg_id)

    def get_message_media(self, message):
        """Get message media content."""
        if not message.check_ack_status():
            raise UnacknowledgedMessage

        msg_type = message.msg_type
        if msg_type in (ImageMessage.msg_type, GifImageMessage.msg_type):
            return self._api_cls.get_msg_img(self.session, message.msg_id)
        elif msg_type == VoiceMessage.msg_type:
            return self._api_cls.get_msg_voice(self.session, message.msg_id)
        elif msg_type == FileMessage.msg_type:
            return self._api_cls.get_msg_media(
                self.session, message.from_user, message.media_id,
                message.filename)

        raise UnsupportedMessage

    def set_user_remark(self, username, remark):
        """Set user wechat remark."""
        self._api_cls.set_user_remark(self.session, username, remark)

    def logout(self):
        """Logout wechat session."""
        self._api_cls.logout(self.session)
