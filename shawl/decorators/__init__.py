# -*- coding: utf-8 -*-
from contextlib import suppress
from typing import Any, Callable, Optional, TypeVar, cast

import wrapt
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.remote.webdriver import WebDriver


def _extract_driver(instance: Any) -> Optional[WebDriver]:
    for value in instance.__dict__.values():
        if isinstance(value, WebDriver):
            return value
    return None


def check_server_error_after(log_level: str = 'SEVERE',
                             bad_msg: str = '500 (Internal Server Error)',
                             driver: WebDriver = None):
    """
    This decorator will check WebDriver logs after execution of
    BasePage class method.

    If there is a record - AssertionError will be raised
    """

    @wrapt.decorator
    def wrapper(wrapped, instance, args, kwargs):
        if instance is None and driver is None:
            raise ValueError('There is no instance. '
                             'Try to place decorator above other decorators '
                             'or set the "driver" keyword for decorator.')
        if instance is not None:
            driver_ = _extract_driver(instance)
        else:
            driver_ = driver
        if driver_ is None:
            raise AttributeError('WebDriver where to find logs is not set. '
                                 'Check if your class has attribute which is '
                                 'instance of "WebDriver". Also, check if you '
                                 'set "driver" keyword for decorator '
                                 'properly. It must be instance of '
                                 '"WebDriver".')
        result = wrapped(*args, **kwargs)
        for log in driver_.get_log('browser'):
            if log.get('level') == log_level:
                message = log.get('message', '')
                if bad_msg in message:
                    raise AssertionError(message)
        return result

    return wrapper


def catch_timeout_error(return_value: Any = False):
    """
    This decorator will catch TimeoutException and return `return_value`.
    """

    @wrapt.decorator
    def wrapper(wrapped, _, args, kwargs) -> Any:
        with suppress(TimeoutException):
            return wrapped(*args, **kwargs)
        return return_value

    return wrapper


__all__ = [
    'check_server_error_after',
    'catch_timeout_error'
    ]
