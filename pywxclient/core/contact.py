
"""WeChat user contact module."""


__all__ = ['WechatContact']


class WechatContact:
    """Wechat contact operation class."""

    group_name_prefix = '@@'
    mp_verify_flag = 8

    def __init__(self, contact_list):
        """Initialize instance."""
        self._contacts = contact_list
        self._personal_contacts = []
        self._mp_contacts = []
        self._group_contacts = []
        self._index = {}

        self._build_contact()

    def _build_contact(self):
        """Classify contacts and build contacts index."""
        for user in self._contacts:
            if self.is_group_user(user):
                self._group_contacts.append(user)
            elif self.is_mp_user(user):
                self._mp_contacts.append(user)
            else:
                self._personal_contacts.append(user)

        for index_key, class_contacts in (
                ('personal', self._personal_contacts),
                ('mp', self._mp_contacts), ('group', self._group_contacts)):
            index_dict = {}
            for idx, user in enumerate(class_contacts):
                username = user['UserName']
                index_dict[username] = idx

            self._index[index_key] = index_dict

    @property
    def personal_contacts(self):
        """Return personal contacts."""
        return self._personal_contacts

    @property
    def mp_contacts(self):
        """Return mp contacts."""
        return self._mp_contacts

    @property
    def group_contacts(self):
        """Return group contacts."""
        return self._group_contacts

    def create_or_update_contact_user(self, user):
        """Add or modify user in contact."""
        if self.is_group_user(user):
            index_obj = self._index['group']
            data_obj = self._group_contacts
        elif self.is_mp_user(user):
            index_obj = self._index['mp']
            data_obj = self._mp_contacts
        else:
            index_obj = self._index['personal']
            data_obj = self._personal_contacts

        username = user['UserName']
        try:
            data_obj[index_obj[username]] = user
        except KeyError:
            data_obj.append(user)
            index_obj[username] = len(data_obj) - 1

    def delete_contact_user(self, user):
        """Delete user in contact."""
        if self.is_group_user(user):
            index_obj = self._index['group']
            data_obj = self._group_contacts
        elif self.is_mp_user(user):
            index_obj = self._index['mp']
            data_obj = self._mp_contacts
        else:
            index_obj = self._index['personal']
            data_obj = self._personal_contacts

        username = user['UserName']
        try:
            data_obj[index_obj[username]] = None
        except KeyError:
            pass

    @classmethod
    def is_group_user(cls, user):
        """Check whether user is a group user.

        :param user: a dict must contain key UserName.

        """
        return user['UserName'].startswith(cls.group_name_prefix)

    @classmethod
    def is_mp_user(cls, user):
        """Check whether user is a media public user.

        :param user: a dict must contain key VerifyFlag.

        """
        return user['VerifyFlag'] & cls.mp_verify_flag
