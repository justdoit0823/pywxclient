
import pytest

from pywxclient.core.contact import WechatContact


class TestContact:

    @pytest.mark.parametrize(
        'user_list', (
            ({'UserName': '@bbbbb', 'VerifyFlag': 0},
             {'UserName': '@@fwewf', 'VerifyFlag': 0},
             {'UserName': '@swfewwf', 'VerifyFlag': 8}),)
    )
    def test_build_contact(self, user_list):
        contact = WechatContact(user_list)

        assert contact.personal_contacts
        assert contact.mp_contacts
        assert contact.group_contacts
