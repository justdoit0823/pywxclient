
import pytest

from pywxclient.core.message import TextMessage, ImageMessage, FileMessage


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

        with pytest.raises(AttributeError):
            msg.new_attr = 'attribute value'

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

        with pytest.raises(AttributeError):
            msg.new_attr = 'attribute value'

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

    @pytest.mark.parametrize(
        'from_user, to_user, media_id, name, size, ext, message', (
            ('@aaaa', '@bbbbb', 'sfwefwfwefw', 'a.pdf', 1231, 'pdf', 'jah'),
            ('@fwewf', '@swefewfwe', 'sfwefwefw', 'g.gif', 123, 'gif', '哈哈'),
            ('@swfewwf', '@wjwejrjwe', 'sfwefwefew', 'x.png', 12, 'png',
             'lele')))
    def test_file_message(
            self, from_user, to_user, media_id, name, size, ext, message):
        msg = FileMessage(
            from_user, to_user, media_id, name, size, ext, message=message)

        assert msg.from_user == from_user
        assert msg.to_user == to_user
        assert msg.message == message
        assert msg.media_id == media_id
        assert msg.filename == name
        assert msg.filesize == size
        assert msg.fileext == ext

        msg_value = msg.to_value()
        assert msg_value['FromUserName'] == from_user
        assert msg_value['ToUserName'] == to_user
        assert media_id in msg_value['Content']
        assert msg_value['Type'] == msg.msg_type

        with pytest.raises(AttributeError):
            msg.new_attr = 'attribute value'

    @pytest.mark.parametrize(
        'msg_value, name, size, ext', ((
            {'MsgId': '1212', 'FromUserName': '@aaaa', 'ToUserName': '@bbbb',
             'MsgType': 49, 'AppMsgType': 6,
             'Content': (
                 '<msg><appmsg appid="wx6618f1cfc6c132f8" sdkver="0"><br/>\t<'
                 'title>haaha.pdf</title><appattach><br/><totallen>14235648</'
                 'totallen><br/>\t\t\t<attachid>@adwqqw12</attachid><fileext>'
                 'pdf</fileext></appattach></appmsg></msg>'),
             'MediaId': '@adwwewewer', 'CreateTime': 1423423234}, 'haaha.pdf',
            14235648, 'pdf'), (
                {'MsgId': '121234', 'FromUserName': '@aaaa',
                 'ToUserName': '@bbbb', 'MsgType': 6, 'Content': (
                     '<appattach><br/><filename>呵呵.png</filename><filesize>'
                     '142356</filesize><br/>\t\t\t<attachid>@adwqqw12'
                     '</attachid><fileext>png</fileext></appattach>'),
                 'MediaId': '@adwwewewerssfwf', 'CreateTime': 142342322422344},
                '呵呵.png', 142356, 'png'))
    )
    def test_parse_file_message(self, msg_value, name, size, ext):
        msg = FileMessage.from_value(msg_value)

        assert msg.msg_id == msg_value['MsgId']
        assert msg.from_user == msg_value['FromUserName']
        assert msg.to_user == msg_value['ToUserName']
        assert msg.message == msg_value['Content']
        assert msg.media_id == msg_value['MediaId']
        assert msg.filename == name
        assert msg.filesize == size
        assert msg.fileext == ext
        assert msg.create_time == int(msg_value['CreateTime'])
        assert msg.check_ack_status()
