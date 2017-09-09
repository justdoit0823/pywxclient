
"""Utility module."""

import functools
import json

from collections import OrderedDict
from urllib.request import unquote
from xml.dom.minidom import Document, parseString


__all__ = [
    'ParseWxRes', 'cookie_to_dict', 'MessageType', 'json_dumps', 'xml2dict',
    'dict2xml', 'call_retry', 'list2orderdict']


class QRUUID:

    code = 0
    uuid = None


class JSWindow:

    code = None
    redirect_uri = None
    synccheck = None
    userAvatar = None

    def __init__(self, qr_uuid=None):

        self.QRLogin = qr_uuid


class ParseException(Exception):
    """Parse javascript exeception."""

    pass


class ParseWxRes:
    """Parse WeChat API response."""

    @classmethod
    def exec_js(cls, js_code, js_locals=None):
        """Execute javascript code in Python."""
        window = JSWindow(QRUUID())

        if js_locals:
            locals().update(js_locals)

        try:
            exec(js_code, None)
        except:
            raise ParseException
        else:
            return window

    @classmethod
    def parse_qrcode_uuid(cls, res_js):
        """Parse qrcode uuid javascript response."""
        window = cls.exec_js(res_js)
        return {'code': window.QRLogin.code, 'uuid': window.QRLogin.uuid}

    @classmethod
    def parse_login(cls, res_js):
        """Parse login javascript response."""
        window = cls.exec_js(res_js)
        return {
            'code': window.code, 'redirect_uri': window.redirect_uri,
            'userAvatar': window.userAvatar}

    @classmethod
    def parse_new_login_page(cls, res_xml):
        """Parse new login page xml response."""
        data = xml2dict(res_xml)['error']
        if 'pass_ticket' in data:
            data['pass_ticket'] = unquote(data['pass_ticket'])

        return data

    @classmethod
    def parse_sync_check(cls, res_js):
        """Parse sync check javascript response."""
        js_locals = {'retcode': 'retcode', 'selector': 'selector'}
        window = cls.exec_js(res_js, js_locals=js_locals)
        return window.synccheck


def cookie_to_dict(cookie):
    """Return cookie attributes as dict."""
    attrs = (
        'version', 'name', 'value', 'port', 'domain', 'path', 'secure',
        'expires', 'discard', 'comment', 'comment_url', 'rfc2109')
    attr_dict = {}
    for attr in attrs:
        attr_val = getattr(cookie, attr, None)
        if attr_val is not None:
            attr_dict[attr] = attr_val

    attr_dict['rest'] = getattr(cookie, '_rest', {})

    return attr_dict


class MessageType(type):
    """Message meta type."""

    _base_slots = (
        'from_user', 'to_user', 'message', 'create_time',
        'local_msg_id', 'msg_id', '_msg_value')

    def __new__(cls, name, bases, namespace, **kwargs):
        """Create a new class instance."""
        ns = dict(namespace)
        slots = ns.get('__slots__') or ()
        if not bases or bases[0] == object:
            # Only add default names to base class's slots
            slots = tuple(set(cls._base_slots + tuple(slots)))

        ns['__slots__'] = tuple(slots)
        new_type = type.__new__(cls, name, bases, ns)

        return new_type


def json_dumps(json_data, compact=False, **kwargs):
    """Dump dict to json string."""
    if compact:
        return json.dumps(json_data, separators=(',', ':'), **kwargs)

    return json.dumps(json_data, **kwargs)


def xml2dict(xml_str):
    """Convert xml document to dict."""
    if isinstance(xml_str, bytes):
        xml_str = xml_str.decode()

    if xml_str.startswith('<?xml'):
        xml_str = '<br/>'.join(xml_str.split('<br/>')[1: -1]).replace('\t', '')

    document = parseString(xml_str)
    root_node = document.childNodes[0]
    data = {}
    DOCUMENT_NODE = root_node.DOCUMENT_NODE
    ELEMENT_NODE = root_node.ELEMENT_NODE
    TEXT_NODE = root_node.TEXT_NODE
    DATA_NODE = root_node.CDATA_SECTION_NODE
    ALL_NODE_TYPE = (DOCUMENT_NODE, ELEMENT_NODE, TEXT_NODE, DATA_NODE)

    def extract_node(node_obj):

        node_type = node_obj.nodeType
        if node_type not in ALL_NODE_TYPE:
            return None

        if node_type == ELEMENT_NODE:
            ele_data = {}
            attrs = {attr: val
                     for attr, val in node_obj.attributes.items()}
            if attrs:
                ele_data['__attrs__'] = attrs

            child_nodes = node_obj.childNodes
            if len(child_nodes) == 1 and (
                    child_nodes[0].nodeType in (TEXT_NODE, DATA_NODE)):
                if not ele_data:
                    return extract_node(child_nodes[0])

                ele_data[node_obj.nodeName] = extract_node(child_nodes[0])
            else:
                for sub_node in child_nodes:
                    ele_data[sub_node.nodeName] = extract_node(sub_node)

            return ele_data
        else:
            return node_obj.nodeValue

    data[root_node.nodeName] = extract_node(root_node)

    return data


def dict2xml(data):
    """Convert dict to xml document."""
    document = Document()

    def create_node(root, node_data):

        for key, val in node_data.items():
            node = document.createElement(key)
            if isinstance(val, dict):
                attrs = val.pop('__attrs__', {})
                for attr, attr_val in attrs.items():
                    node.setAttribute(attr, attr_val)

                create_node(node, val)
            elif isinstance(val, (tuple, list)):
                for sub_data in val:
                    create_node(node, sub_data)
            else:
                node.appendChild(document.createTextNode(str(val)))

            root.appendChild(node)

    create_node(document, data)

    return document.childNodes[0].toxml()


def call_retry(retry_exceptions, retries=3):
    """Auto retry when exception occurs.

    :param retry_exceptions: catch exception tuple.
    :param retries: retry times.
    """
    def func_decorator(func):

        @functools.wraps(func)
        def wrapper(*args, **kwargs):

            call_retries = kwargs.pop('retries', None)
            once_retries = min(
                call_retries if call_retries is not None else retries, 0)
            loop_count = once_retries + 1
            while loop_count > 0:
                try:
                    return func(*args, **kwargs)
                except retry_exceptions:
                    if once_retries == 0:
                        raise

                    loop_count -= 1

            raise Warning('Retry exceeds {0} times when calling {1}'.format(
                retries, func.__name__))

        return wrapper

    return func_decorator


def list2orderdict(key_list, val_list):
    """Return a ordered dict with two lists."""
    return OrderedDict(zip(key_list, val_list))
