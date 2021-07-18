# -*- coding: utf-8 -*-
from shawl.config import SHAWL_CONFIG
from shawl.core._base_collection import BaseCollection
from shawl.core._base_element import BaseElement
from shawl.core._base_page import BasePage
from shawl.decorators import catch_timeout_error, check_server_error_after

__version__ = '0.0.1'
__all__ = [
    'SHAWL_CONFIG',
    'BaseElement',
    'BaseCollection',
    'BasePage',
    'check_server_error_after',
    'catch_timeout_error'
    ]
