

__all__ = [
    'WaitScanQRCode', 'AuthorizeTimeout', 'UnknownWindowCode',
    'SessionInitFailure', 'NotifyStatusFailure', 'APIResponseError',
    'SessionExpiredError', 'MessageAlreadyAcknowledge', 'RequestError',
    'UnacknowledgedMessage']


class UnknownWindowCode(Exception):
    """"""
    pass


class WaitScanQRCode(Warning):
    """"""
    pass


class AuthorizeTimeout(Exception):
    """"""
    pass


class SessionInitFailure(Exception):
    """WeChat session init failed."""
    pass


class NotifyStatusFailure(Warning):
    """"""
    pass


class APIResponseError(Exception):
    """WeChart HTTP api response error."""
    pass


class SessionExpiredError(Exception):
    """Session expired error."""
    pass


class UnsupportedMessage(Exception):
    """Unsupported message error."""
    pass


class UnacknowledgedMessage(Exception):
    """Unacknowledge message error."""
    pass


class MessageAlreadyAcknowledge(Exception):
    """Already acknowledged mesage error."""
    pass


class RequestError(IOError):
    """Network request error."""
    pass


class LoginError(Exception):
    """Login wechat failed error."""
    pass
