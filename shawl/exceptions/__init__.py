# -*- coding: utf-8 -*-
from selenium.common.exceptions import WebDriverException


class WindowHandlesException(Exception):
    pass


class NoSuchElementsException(WebDriverException):
    pass


class NoneValuesInYamlException(Exception):
    pass


class InitNotFoundException(Exception):
    pass
