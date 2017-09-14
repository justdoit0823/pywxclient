
"""WeChat message parse and construct module."""

import html
import time

from pywxclient.core.exception import UnsupportedMessage
from pywxclient.utils import MessageType, dict2xml, xml2dict


__all__ = [
    'TextMessage', 'ImageMessage', 'GifImageMessage', 'VoiceMessage',
    'FileMessage', 'VideoMessage', 'ExtendMessage', 'LocationShareMessage',
    'BusinessCardMessage', 'TransferMessage', 'ChatLogMessage',
    'ShareLinkMessage', 'WeAppMessage', 'NoticeMessage', 'RevokeMessage',
    'StatusNotifyMessage', 'parse_message']


_specified_appmsg_appid = 'wxeb7ec651dd0aefa9'
_supported_message_parser = {}


class MessageBase(metaclass=MessageType):
    """WeChat message base class."""

    msg_type = None

    def __init__(
            self, from_user, to_user, message, local_msg_id=None,
            create_time=None, msg_id=None):
        """Initialize message object."""
        self.from_user = from_user
        self.to_user = to_user
        self.message = message
        self.create_time = int(create_time) if create_time else time.time()
        self.local_msg_id = local_msg_id or self.get_local_msg_id()
        self.msg_id = msg_id
        self._msg_value = None

    def get_local_msg_id(self):
        """Generate local message id based on unix timestamp."""
        return int(self.create_time * 1000000)

    def get_base_value(self):
        return {
            'LocalID': self.local_msg_id, 'ClientMsgId': self.local_msg_id}

    def get_body_value(self):
        """Return message body."""
        return {
            'Type': self.msg_type, 'Content': self.get_message_content(),
            'FromUserName': self.from_user, 'ToUserName': self.to_user}

    def to_value(self):
        """Return constructed message value."""
        if self._msg_value:
            return self._msg_value

        base_value = self.get_base_value()
        body_value = self.get_body_value()
        body_value.update(**base_value)

        self._msg_value = body_value

        return self._msg_value

    def get_message_content(self):
        """Return formatted message content."""
        return self.message

    def ack(self, local_msg_id, msg_id):
        """Acknowledge message has been sent successfully."""
        assert local_msg_id == str(
            self.local_msg_id), 'Invalid message acknowledge.'
        self.msg_id = msg_id

    def check_ack_status(self):
        """Check whether this message has been acknowledged."""
        return self.msg_id is not None

    @classmethod
    def from_value(cls, msg_value):
        """Construct a message object from message value."""
        msg_id = msg_value['MsgId']
        from_username = msg_value['FromUserName']
        to_username = msg_value['ToUserName']
        message = html.unescape(msg_value['Content'])
        create_time = int(msg_value['CreateTime'])
        local_msg_id = str(create_time * 1000000)
        msg_obj = cls(
            from_username, to_username, message, local_msg_id=local_msg_id,
            create_time=create_time)
        msg_obj.ack(local_msg_id, msg_id)
        return msg_obj


class TextMessage(MessageBase):
    """WeChat text message."""

    msg_type = 1


class StatusNotifyMessage(MessageBase):
    """WeChat user status notify message."""

    msg_type = 51


class MediaMessagebase(MessageBase):
    """Media message base class."""

    __slots__ = ('media_id',)

    def __init__(
            self, from_user, to_user, media_id, message='', local_msg_id=None,
            create_time=None, msg_id=None):

        super(MediaMessagebase, self).__init__(
            from_user, to_user, message, local_msg_id=local_msg_id,
            create_time=create_time, msg_id=msg_id)
        self.media_id = media_id

    @classmethod
    def from_value(cls, msg_value):
        """Construct a message object from message value."""
        msg_id = msg_value['MsgId']
        from_username = msg_value['FromUserName']
        to_username = msg_value['ToUserName']
        media_id = msg_value['MediaId']
        content = html.unescape(msg_value['Content'])
        create_time = int(msg_value['CreateTime'])
        local_msg_id = str(create_time * 1000000)
        msg_obj = cls(
            from_username, to_username, media_id, message=content,
            local_msg_id=local_msg_id, create_time=create_time)
        msg_obj.ack(local_msg_id, msg_id)
        return msg_obj

    def get_message_content(self):
        return self.media_id

    def get_body_value(self):
        """Return media message body value."""
        return {
            'Type': self.msg_type, 'MediaId': self.get_message_content(),
            'FromUserName': self.from_user, 'ToUserName': self.to_user}


class ImageMessage(MediaMessagebase):
    """WeChat image message."""

    msg_type = 3


class GifImageMessage(MediaMessagebase):
    """WeChat gif image message."""

    msg_type = 47


class VoiceMessage(MediaMessagebase):
    """WeChat voice message."""

    msg_type = 34


class FileMessage(MediaMessagebase):
    """WeChat file message."""

    msg_type = 6

    __slots__ = ('filename', 'filesize', 'fileext')

    def __init__(
            self, from_user, to_user, media_id, filename, filesize, fileext,
            local_msg_id=None, create_time=None, msg_id=None):
        """Initialize `FileMessage` instance."""
        super(FileMessage, self).__init__(
            from_user, to_user, media_id, local_msg_id=local_msg_id,
            create_time=create_time, msg_id=msg_id)
        self.filename = filename
        self.filesize = filesize
        self.fileext = fileext

    def get_body_value(self):
        """Return message body."""
        return super(MediaMessagebase, self).get_body_value()

    def get_message_content(self):
        """Return file message content."""
        msg_data = {
            'appmsg': {
                '__attrs__': {'appid': _specified_appmsg_appid, 'sdkver': ''},
                'title': self.filename, 'des': '', 'action': '',
                'type': self.msg_type, 'content': self.message, 'url': '',
                'lowurl': '', 'appattach': {
                    'totallen': self.filesize, 'attachid': self.media_id,
                    'fileext': self.fileext}, 'extinfo': ''
            }
        }

        return dict2xml(msg_data)

    @classmethod
    def from_value(cls, msg_value):
        """Construct a message object from message value."""
        msg_id = msg_value['MsgId']
        msg_type = msg_value['MsgType']
        from_username = msg_value['FromUserName']
        to_username = msg_value['ToUserName']
        media_id = msg_value['MediaId']
        create_time = msg_value['CreateTime']
        local_msg_id = str(create_time * 1000000)
        if msg_type == ExtendMessage.msg_type:
            msg_data = xml2dict(html.unescape(msg_value['Content']))['msg']
            appmsg_data = msg_data['appmsg']
            appattach = appmsg_data['appattach']
            filename = appmsg_data['title']
            filesize = appattach['totallen']
            fileext = appattach['fileext']
        else:
            appmsg_data = xml2dict(html.unescape(msg_value['Content']))
            appattach = appmsg_data['appattach']
            filename = appattach['filename']
            filesize = int(appattach['filesize'])
            media_id = media_id or appattach['attachid']
            fileext = appattach['fileext']

        msg_obj = cls(
            from_username, to_username, media_id, filename, filesize, fileext,
            create_time=create_time, local_msg_id=local_msg_id)
        msg_obj.ack(local_msg_id, msg_id)
        return msg_obj


class VideoMessage(MediaMessagebase):
    """WeChat video message."""

    msg_type = 43


class ExtendMessage(MessageBase):
    """Extend message."""

    msg_type = 49


class LocationShareMessage(MessageBase):
    """Location share message."""

    msg_type = 17

    @classmethod
    def from_value(cls, msg_value):
        """Construct message instance."""
        msg_id = msg_value['MsgId']
        from_username = msg_value['FromUserName']
        to_username = msg_value['ToUserName']
        content = html.unescape(msg_value['Content'])
        xml_value = xml2dict(content)
        message = xml_value['msg']['appmsg']['title']
        create_time = int(msg_value['CreateTime'])
        local_msg_id = str(create_time * 1000000)
        msg_obj = cls(
            from_username, to_username, message, local_msg_id=local_msg_id,
            create_time=create_time)
        msg_obj.ack(local_msg_id, msg_id)
        return msg_obj


class BusinessCardMessage(MessageBase):
    """Business card message."""

    msg_type = 42


class TransferMessage(MessageBase):
    """Transfer message."""

    msg_type = 2000


class ChatLogMessage(MessageBase):
    """Chatlog message."""

    msg_type = 0


class ShareLinkMessage(MessageBase):
    """Link share message."""

    msg_type = 5


class WeAppMessage(MessageBase):
    """WeApp message."""

    msg_type = 33


class NoticeMessage(MessageBase):
    """WeChat notice message."""

    msg_type = 10000


class RevokeMessage(MessageBase):
    """WeChat revoke message."""

    msg_type = 10002


def parse_message(msg_value):
    """Parse mesage value to specific MesageBase object."""
    msg_type = msg_value['MsgType']
    try:
        msg_parser = _supported_message_parser[msg_type]
    except KeyError:
        raise UnsupportedMessage
    else:
        if msg_type == ExtendMessage.msg_type:
            app_msg_type = msg_value['AppMsgType']
            try:
                msg_parser = _supported_message_parser[app_msg_type]
            except KeyError:
                raise UnsupportedMessage

        return msg_parser(msg_value)


def _register_message_parser(msg_parsers):
    """Register message parsers."""
    for parser_type, parser in msg_parsers:
        _supported_message_parser[parser_type] = parser


_register_message_parser(
    (msg.msg_type, msg.from_value) for msg in (
        TextMessage, ImageMessage, GifImageMessage, VoiceMessage, VideoMessage,
        StatusNotifyMessage, NoticeMessage, RevokeMessage, FileMessage,
        ExtendMessage, LocationShareMessage, BusinessCardMessage,
        TransferMessage, ShareLinkMessage, ChatLogMessage, WeAppMessage))
