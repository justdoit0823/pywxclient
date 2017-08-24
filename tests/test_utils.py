
import pytest

from collections import OrderedDict

from pywxclient.utils import dict2xml, list2orderdict, xml2dict


@pytest.mark.parametrize(
    't_list, t_dict', (
        ((('a', 'b'), (12, 123)), OrderedDict((('a', 12), ('b', 123)))),
    ))
def test_list2orderdict(t_list, t_dict):
    o_dict = list2orderdict(*t_list)
    assert o_dict == t_dict


@pytest.mark.parametrize(
    'xml', (
        '<res><code>0</code><data>hello world</data></res>',
    ))
def test_xml2dict(xml):
    data = xml2dict(xml)

    assert data['res']['code'] == '0'
    assert data['res']['data'] == 'hello world'


@pytest.mark.parametrize(
    'data, e_xml', (
        ({'res': [{'code': 0}, {'data': 'hello world'}]},
         '<res><code>0</code><data>hello world</data></res>'),
    ))
def test_dict2xml(data, e_xml):
    xml = dict2xml(data)

    assert xml == e_xml


@pytest.mark.parametrize(
    'data, e_xml', (
        ((list2orderdict(('res',), (
            list2orderdict(('code', 'data', '__attrs__'), (0, 'hello world', list2orderdict(('x', 'y'), ('h', 'z')))),))),
         '<res x="h" y="z"><code>0</code><data>hello world</data></res>'),
    ))
def test_dict2xml_attr(data, e_xml):
    xml = dict2xml(data)

    assert xml == e_xml
