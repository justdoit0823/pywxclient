
"""Exception module."""

__all__ = [
    'WaitScanQRCode', 'AuthorizeTimeout', 'UnknownWindowCode',
    'SessionInitFailure', 'NotifyStatusFailure', 'APIResponseError',
    'SessionExpiredError', 'MessageAlreadyAcknowledge', 'RequestError',
    'UnacknowledgedMessage']


class UnknownWindowCode(Exception):
    """Unkonw window code exeception."""

    pass


class WaitScanQRCode(Warning):
    """Wait scanning QRCode exception."""

    pass


class AuthorizeTimeout(Exception):
    """Authorization timeout exception."""

    pass


class SessionInitFailure(Exception):
    """WeChat session init failed."""

    pass


class NotifyStatusFailure(Warning):
    """Notify status exception."""

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
