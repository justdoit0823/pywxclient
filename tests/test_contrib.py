
import pytest

from pywxclient.contrib import HTTPFile


@pytest.mark.parametrize(
    'url, content_disposition, name', (
        ('https://foo.com/img_abc', 'attachment; filename="haha.jpg"',
         'haha.jpg'),
        ('https://foo.com/img_abc', '', 'img_abc'),
        ('https://foo.com/img_abc', 'attachment; filename="哈哈.jpg"',
         '哈哈.jpg'),
        ('https://foo.com/img_abc',
         'attachment; filename="å\x93\x88å\x93\x88.jpg"', '哈哈.jpg')
    )
)
def test_http_file_name(mocker, url, content_disposition, name):

    class Res:

        code = 200
        content = b'hahaha'
        headers = {
            'Content-Type': 'image/png',
            'Content-Disposition': content_disposition}

    get_func = mocker.patch('requests.get')
    get_func.return_value = Res

    file_obj = HTTPFile(url)

    assert file_obj.name == name
