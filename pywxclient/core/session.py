
"""WeChat session manage module."""

import copy
import requests

from abc import ABCMeta, abstractmethod

from pywxclient import __version__
from pywxclient.utils import cookie_to_dict
from pywxclient.core.exception import RequestError
from pywxclient.core.api import WeChatAPI


__all__ = ['Session']


class WxSession:

    def __init__(self, skey, pass_ticket, wxsid, wxuin, isgrayscale=0):
        """Initialize WeChat session."""
        self._skey = skey
        self._pass_ticket = pass_ticket
        self._wxsid = wxsid
        self._wxuin = wxuin
        self._isgrayscale = isgrayscale
        self._sync_key = {}

    def sync_session_key(self, sync_key):
        """Save sync key in session."""
        self._sync_key = copy.copy(sync_key)

    def to_dict(self):
        """Return session data."""
        return {
            'skey': self._skey, 'pass_ticket': self._pass_ticket,
            'wxsid': self._wxsid, 'wxuin': self._wxuin,
            'isgrayscale': self._isgrayscale, 'sync_key': self._sync_key}

    @classmethod
    def from_dict(cls, session_data):
        """Initialize a WxSession from dict."""
        skey = session_data['skey']
        pass_ticket = session_data['pass_ticket']
        wxsid = session_data['wxsid']
        wxuin = session_data['wxuin']
        isgrayscale = session_data['isgrayscale']
        sync_key = session_data.get('sync_key')

        wx_session = cls(
            skey, pass_ticket, wxsid, wxuin, isgrayscale=isgrayscale)

        if sync_key:
            wx_session.sync_session_key(copy.copy(sync_key))

        return wx_session


class RequestSession(metaclass=ABCMeta):
    """A RequestSession class for hanlding http request."""

    @abstractmethod
    def load(self, cookies):
        """Load sesssion from cookie dict."""
        raise NotImplementedError

    @abstractmethod
    def dump(self):
        """Return session cookie dict."""
        raise NotImplementedError

    @abstractmethod
    def request(self, method, url, **kwargs):
        """Do http request."""
        raise NotImplementedError

    @abstractmethod
    def get(self, url, **kwargs):
        """Do GET http request."""
        raise NotImplementedError

    @abstractmethod
    def post(self, url, **kwargs):
        """Do POST http request."""
        raise NotImplementedError


RequestSession.register(requests.Session)


class RequestsSession(requests.Session):
    """Request session implementation of requests.Session."""

    user_agent = 'pywxclient/' + __version__
    default_headers = {'User-Agent': user_agent}

    def load(self, cookies):
        """Load cookie dict into cookiejar object."""
        for cookie in cookies:
            name = cookie.pop('name')
            value = cookie.pop('value')
            cookie_obj = requests.cookies.create_cookie(name, value, **cookie)
            self.cookies.set_cookie(cookie_obj)

    def dump(self):
        """Dump session cookies as list."""
        all_cookies = []
        for cookie in self.cookies:
            all_cookies.append(cookie_to_dict(cookie))

        return all_cookies

    def request(self, method, url, **kwargs):

        headers = kwargs.get('headers')
        if headers:
            headers = dict(headers)
            if 'User-Agent' not in map(str.title, headers.keys()):
                headers['User-Agent'] = self.user_agent
        else:
            headers = self.default_headers

        kwargs['headers'] = headers

        try:
            return super(RequestsSession, self).request(method, url, **kwargs)
        except requests.RequestException:
            raise RequestError

    def get(self, url, **kwargs):

        return self.request('GET', url, **kwargs)

    def post(self, url, **kwargs):

        return self.request('POST', url, **kwargs)


class Session:
    """WeChat client session class."""

    def __init__(
            self, request_session_cls=RequestsSession, session_data=None,
            endpoint=None, **kwargs):
        """Initialize wechat session."""
        self._wx_session = None
        self._wx_endpoint = endpoint
        self._authorized = False
        self._online = False

        if not issubclass(request_session_cls, RequestSession):
            raise TypeError('Invalid request session class.')
        else:
            self._req_session = request_session_cls(**kwargs)

        self.get = self._req_session.get
        self.post = self._req_session.post
        self.request = self._req_session.request

        if session_data:
            self.load(session_data)

    def finish_authorize(self, endpoint):
        """Session has authorized successfully."""
        self._authorized = True
        self._wx_endpoint = endpoint

    def sync(self, sync_key):
        """Sync session state."""
        self._wx_session.sync_session_key(sync_key)
        self._online = self._online or True

    def load(self, session_data):
        """Load session from data."""
        wx_session_data = session_data['wx_session']
        if wx_session_data:
            self._wx_session = WxSession.from_dict(wx_session_data)
            self._authorized = True
            self._online = True

        self._req_session.load(session_data['req_session'])
        self._wx_endpoint = session_data.get('wx_endpoint')

    def is_active(self):
        """Check whether session is active."""
        return self._online

    @property
    def authorized(self):
        """Indicate whether session has authorized."""
        return self._authorized

    @property
    def wx_endpoint(self):
        """Return wechat session endpoint."""
        if not self._wx_endpoint:
            self._wx_endpoint = WeChatAPI.get_wx_endpoint()

        return self._wx_endpoint

    @wx_endpoint.setter
    def wx_endpoint(self, endpoint):
        """Set wechat session endpoint."""
        self._wx_endpoint = endpoint

    def initialize_wx_session(self, wx_session_data):
        """Initialize `WxSession` instance."""
        self._wx_session = WxSession.from_dict(wx_session_data)

    def get_wx_session_data(self):
        """Return `WxSession` related data."""
        return self._wx_session.to_dict() if self._wx_session else {}

    def get_session_cookies(self):
        """Return session cookies."""
        return self._req_session.cookies

    def dump(self):
        """Dump session as a dict."""
        wx_session = self.get_wx_session_data()
        req_session = self._req_session.dump()
        return {
            'wx_session': wx_session, 'req_session': req_session,
            'wx_endpoint': self._wx_endpoint}

    def close(self):
        """Close session."""
        if self._req_session:
            self._req_session.close()
