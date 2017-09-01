
"""File object module."""

import io
import os
import requests
import time

from hashlib import md5


__all__ = ['LocalFile', 'HTTPFile']


class File:

    t_format = '%a %b %d %Y %H:%M:%S GMT%z (CST)'

    short_type_mapping = {
        'jpg': 'pic',
        'jpeg': 'pic',
        'png': 'pic',
        'icon': 'pic',
        'gif': 'pic',
        'doc': 'doc',
        'txt': 'doc',
        'pdf': 'doc',
        'mp4': 'video',
        'avi': 'video'
    }

    mime_prefix_mapping = {
        'pic': 'image/', 'doc': 'application/', 'video': 'video/'}

    def __init__(self, file_bytes):

        self._stream = io.BytesIO(file_bytes)
        self._size = len(file_bytes)
        self.name = ''

    @property
    def size(self):
        """Return file size."""
        return self._size

    @property
    def ext(self):
        """Return file ext."""
        return self._type

    @property
    def md5(self):
        return md5(self._stream.getbuffer()).hexdigest()

    @property
    def last_mtime(self):
        return time.strftime(self.t_format, time.gmtime(self._last_mtime))

    def short_type(self):
        return self.short_type_mapping.get(self._type, 'doc')

    def media_type(self):
        short_type = self.short_type()
        return self.mime_prefix_mapping[short_type] + self._type

    def read(self, size=None):
        return self._stream.read(size)

    def seekable(self):
        return self._stream.seekable()

    def seek(self, pos, whence=0):
        return self._stream.seek(pos, whence)

    def closed(self):
        return self._stream.closed()

    def close(self):
        return self._stream.close()

    def fileno(self):
        return self._stream.fileno()


class LocalFile(File):
    """Local disk file."""

    def __init__(self, file_path):
        """Initialize `LocalFile` instance."""
        with open(file_path, 'rb') as f:
            super(LocalFile, self).__init__(f.read())

        self.name = os.path.basename(file_path)
        __, file_ext = os.path.splitext(self.name)
        self._type = file_ext[1:]
        self._last_mtime = os.stat(file_path).st_mtime


class HTTPFile(File):
    """HTTP file."""

    def __init__(self, file_url):
        """Initialize `HTTPFile` instance."""
        res = requests.get(file_url)
        super(HTTPFile, self).__init__(res.content)
        self.name = os.path.basename(file_url)
        self._type = res.headers['Content-Type'].split('/')[1]
        self._last_mtime = time.time()
