import argparse
import importlib
import logging
import sys
from io import StringIO
from logging import Logger, StreamHandler
from unittest.mock import patch
from cysystemd import journal

import pytest
from lologen import generate_random_string, exec_logger
import lologen
from logfmter import Logfmter
import logging_json


class TestColorFormatter:
    def format(self, record):
        return record


class TestFormatter:
    def format(self, record):
        return self.get_test_assert_val()

    def get_test_assert_val(self):
        return 123

@pytest.fixture
def arguments_fixture_journald_unstructured():
    a = argparse.Namespace(
        name='test_name',
        type='journald',
        level='debug',
        stream='stdout',
        color='always',
        format='unstructured')
    yield a


def arguments_formatted_color_builder(name='', color='', format=''):
    a = argparse.Namespace(color=color, name=name, format=format)
    return a


@pytest.fixture
def arguments_fixture_console_unstructured():
    a = argparse.Namespace(
        #name='test_name',
        type='console',
        level='debug',
        stream='stdout',
        color='always',
        format='unstructured')
    yield a


def test_generate_random_string():
    str_len = len(generate_random_string())
    assert str_len >= 10
    assert str_len <= 20


def test_exec_logger_console_unstructed(arguments_fixture_console_unstructured):
    lologen.arguments = arguments_fixture_console_unstructured
    lologen.arguments.name = 'arguments_fixture_console_unstructured'
    result = exec_logger()
    assert isinstance(result, Logger) is True
    assert len(result.handlers) == 1
    assert isinstance(result.handlers[0], StreamHandler)


def test_exec_logger_journald_unstructed(arguments_fixture_journald_unstructured):
    lologen.arguments = arguments_fixture_journald_unstructured
    lologen.arguments.name = 'arguments_fixture_journald_unstructured'
    result = exec_logger()
    assert isinstance(result, Logger) is True
    assert len(result.handlers) == 1
    assert isinstance(result.handlers[0], journal.JournaldLogHandler)


def test_create_console_handler():
    lologen.arguments = arguments_formatted_color_builder(
        'arguments_console_color_always',
        'always',
        'unstructured'
    )

    handler = lologen.create_console_handler()
    assert isinstance(handler, StreamHandler)
    assert isinstance(handler.formatter, lologen.MySuperColorFormatter)

    lologen.arguments = arguments_formatted_color_builder(
        'arguments_console_color_always_output_value_error',
        'always',
        'unstructured'
    )
    console_log_output = 'something'
    error_message = f"{lologen.ERROR_VALUE} '%s'" % console_log_output
    with pytest.raises(ValueError, match=error_message):
        handler = lologen.create_console_handler(console_log_output=console_log_output)

    lologen.arguments = arguments_formatted_color_builder(
        'arguments_console_color_always_log_level_value_error',
        'always',
        'unstructured'
    )
    console_log_level = 'something'
    error_message = "Unknown level: %r" % console_log_level.upper()
    with pytest.raises(ValueError, match=error_message):
        handler = lologen.create_console_handler(console_log_level=console_log_level)


def test_create_http_handler():
    args = arguments_formatted_color_builder(
        'arguments_http_color_always',
        'always',
        'unstructured'
    )
    web_host = 'localhost'
    web_port = '80'
    web_method = 'GET'
    args.__setattr__('web_host', web_host)
    args.__setattr__('web_port', web_port)
    args.__setattr__('web_method', web_method)
    lologen.arguments = args
    handler = lologen.create_http_handler()
    assert isinstance(handler, logging.handlers.HTTPHandler)
    assert handler.url == f"http://{web_host}:{web_port}"
    assert handler.method == web_method

    args.name = 'arguments_http_color_always_log_level_value_error'
    lologen.arguments = args
    console_log_level = 'something'
    error_message = "Unknown level: %r" % console_log_level.upper()
    with pytest.raises(ValueError, match=error_message):
        handler = lologen.create_http_handler(console_log_level=console_log_level)


def test_create_file_handler():
    lologen.arguments = arguments_formatted_color_builder(
        'arguments_file_color_always',
        'never',
        'unstructured'
    )
    lologen.arguments.__setattr__('path_file', '/tmp/log')
    handler = lologen.create_file_handler()
    assert isinstance(handler, logging.FileHandler)
    assert isinstance(handler.formatter, lologen.NonColorFormatter)


def test_create_journald_handler():
    lologen.arguments = arguments_formatted_color_builder(
        'arguments_journald_color_always',
        'never',
        'unstructured'
    )
    handler = lologen.create_journald_handler()
    assert isinstance(handler, journal.JournaldLogHandler)
    assert isinstance(handler.formatter, lologen.NonColorFormatter)

    lologen.arguments = arguments_formatted_color_builder(
        'arguments_journald_color_always_log_level_value_error',
        'never',
        'unstructured'
    )
    console_log_level = 'something'
    error_message = "Unknown level: %r" % console_log_level.upper()
    with pytest.raises(ValueError, match=error_message):
        handler = lologen.create_journald_handler(console_log_level=console_log_level)


def test_create_logger():
    name = 'random_name'
    lgr = lologen.create_logger(name, False)
    assert isinstance(lgr, Logger)
    assert lgr.name == name


def test_log_format():
    lologen.arguments = argparse.Namespace(format='unstructured')
    lf = lologen.log_format(True)
    assert isinstance(lf, lologen.MySuperColorFormatter)
    assert isinstance(lf.original_formatter, logging.Formatter)

    lologen.arguments = argparse.Namespace(format='logfmt')
    lf = lologen.log_format(False)
    assert isinstance(lf, lologen.NonColorFormatter)
    assert isinstance(lf.original_formatter, Logfmter)

    lologen.arguments = argparse.Namespace(format='json')
    lf = lologen.log_format(False)
    assert isinstance(lf.original_formatter, logging_json.JSONFormatter)

    lologen.arguments = argparse.Namespace(format='unknown')
    with pytest.raises(ValueError, match=f"{lologen.ERROR_VALUE} '%s'" % lologen.arguments.format):
        lologen.log_format(False)


def test_use_color():
    lologen.arguments = argparse.Namespace(color='always')
    assert lologen.use_color() is True
    lologen.arguments = argparse.Namespace(color='never')
    assert lologen.use_color() is False
    lologen.arguments = argparse.Namespace(color='unknown')
    with pytest.raises(ValueError, match=f"{lologen.ERROR_VALUE} '%s'" % lologen.arguments.color):
        lologen.use_color()


def test_non_color_formatter():


    cls = lologen.NonColorFormatter(original_formatter=1)
    assert cls.original_formatter == 1
    fmt = TestFormatter()
    cls = lologen.NonColorFormatter(fmt)
    assert cls.format(record=logging.LogRecord(
        name='',
        level='debug',
        pathname='/',
        lineno=1,
        msg='msg',
        args=[True],
        exc_info=True
    )) == fmt.get_test_assert_val()

def test_my_super_color_formatter():

    cls = lologen.MySuperColorFormatter(original_formatter=1)
    assert cls.original_formatter == 1
    fmt = TestColorFormatter()
    cls = lologen.MySuperColorFormatter(fmt)
    msg = 'message'
    record = logging.LogRecord(
        name='',
        level='DEBUG',
        pathname='/',
        lineno=1,
        msg=msg,
        args=[True],
        exc_info=True,

    )
    record.levelname = 'DEBUG'
    record.levelno = logging.DEBUG
    changed_record = cls.format(record)
    assert changed_record.msg == f"\x1b[0;36m{msg}\x1b[0m"

