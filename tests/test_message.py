
import pytest

from pywxclient.core.message import TextMessage, ImageMessage


class TestMessage:

    @pytest.mark.parametrize(
        'from_user, to_user, message', (
            ('@aaaa', '@bbbbb', 'haahahha'),
            ('@fwewf', '@swefewfwe', 'heeheheh'),
            ('@swfewwf', '@wjwejrjwe', '你好')))
    def test_text_message(self, from_user, to_user, message):
        msg = TextMessage(from_user, to_user, message)

        assert msg.from_user == from_user
        assert msg.to_user == to_user
        assert msg.message == message

        msg_value = msg.to_value()
        assert msg_value['FromUserName'] == from_user
        assert msg_value['ToUserName'] == to_user
        assert msg_value['Content'] == message
        assert msg_value['Type'] == msg.msg_type

    @pytest.mark.parametrize(
        'msg_value', (
            {'MsgId': '12123', 'FromUserName': '@aaaa', 'ToUserName': '@bbbb',
             'Content': 'hello', 'CreateTime': 1423423234},
            {'MsgId': '121232', 'FromUserName': '@ccc', 'ToUserName': '@ddd',
             'Content': '你好', 'CreateTime': 1423423234123},
            {'MsgId': '121232', 'FromUserName': '@ccc', 'ToUserName': '@ddd',
             'Content': '你好', 'CreateTime': '1423423234123'}))
    def test_parse_text_message(self, msg_value):
        msg = TextMessage.from_value(msg_value)

        assert msg.msg_id == msg_value['MsgId']
        assert msg.from_user == msg_value['FromUserName']
        assert msg.to_user == msg_value['ToUserName']
        assert msg.message == msg_value['Content']
        assert msg.create_time == int(msg_value['CreateTime'])
        assert msg.check_ack_status()

    @pytest.mark.parametrize(
        'from_user, to_user, media_id', (
            ('@aaaa', '@bbbbb', 'sfwefwfwefw'),
            ('@fwewf', '@swefewfwe', 'sfwefwefw'),
            ('@swfewwf', '@wjwejrjwe', 'sfwefwefew')))
    def test_image_message(self, from_user, to_user, media_id):
        msg = ImageMessage(from_user, to_user, media_id)

        assert msg.from_user == from_user
        assert msg.to_user == to_user
        assert msg.message == ''
        assert msg.media_id == media_id

        msg_value = msg.to_value()
        assert msg_value['FromUserName'] == from_user
        assert msg_value['ToUserName'] == to_user
        assert msg_value['MediaId'] == media_id
        assert msg_value['Type'] == msg.msg_type

    @pytest.mark.parametrize(
        'msg_value', (
            {'MsgId': '121231', 'FromUserName': '@aaaa', 'ToUserName': '@bbbb',
             'Content': '', 'MediaId': '@adwwefw', 'CreateTime': 1423423234},
            {'MsgId': '121231', 'FromUserName': '@aaaa', 'ToUserName': '@bbbb',
             'Content': '', 'MediaId': '@adwwefw', 'CreateTime': '1423423234'},
            {'MsgId': '1223121', 'FromUserName': '@ccc', 'ToUserName': '@ddd',
             'Content': '', 'MediaId': '@afwfwfw',
             'CreateTime': 1423423234123})
    )
    def test_parse_image_message(self, msg_value):
        msg = ImageMessage.from_value(msg_value)

        assert msg.msg_id == msg_value['MsgId']
        assert msg.from_user == msg_value['FromUserName']
        assert msg.to_user == msg_value['ToUserName']
        assert msg.message == ''
        assert msg.media_id == msg_value['MediaId']
        assert msg.create_time == int(msg_value['CreateTime'])
        assert msg.check_ack_status()
