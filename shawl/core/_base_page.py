# -*- coding: utf-8 -*-
import sys
from collections import namedtuple
from inspect import getfile
from os.path import exists, isfile, join
from time import sleep
from types import ModuleType
from typing import Any, Dict, List, Optional, Union, cast

import yaml
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.expected_conditions import (
    alert_is_present,
    frame_to_be_available_and_switch_to_it,
    new_window_is_opened,
    number_of_windows_to_be,
    title_contains,
    title_is,
    url_changes,
    url_contains,
    url_matches,
    url_to_be
)

from ..config import SHAWL_CONFIG as CONFIG
from ..decorators import check_server_error_after
from ..exceptions import InitNotFoundException, NoneValuesInYamlException
from ..utils._waits import wait_until
from ._base_collection import BaseCollection
from ._base_element import BaseElement

_INVISIBLE = namedtuple('_INVISIBLE', ['all_invisible', 'not_invisible'])
_PRESENT = namedtuple('_PRESENT', ['all_present', 'not_present'])

ShawlElems = Union[BaseElement, BaseCollection]


def _get_list(item: Union[List[str], str]) -> List[str]:
    if isinstance(item, list):
        return item
    return [item] if isinstance(item, str) else list()


def _load_page(file: str, path: str) -> Dict[str, str]:
    """
    Load yaml file as dict
    """
    # pylint: disable=consider-using-with
    file_path: str = join(path, file)
    if not exists(file_path) or not isfile(file_path):
        return dict()
    return yaml.full_load(open(file_path, encoding='utf-8')) or dict()


def _check_not_none_values(source: Dict[str, str], yaml_file: str):
    if not all(source.values()):
        raise NoneValuesInYamlException(
            f'There is None value in {yaml_file} file. '
            'Check that all keys have not None values')
    for v in source.values():
        if isinstance(v, dict):
            _check_not_none_values(v, yaml_file)


def _merge_page_dicts(source: Dict[str, Dict[str, Any]],
                      new: Dict[str, Dict[str, Any]]):
    """
    Merge two yaml dicts, so that previously loaded element_name_html_element
    will not be overwritten
    """
    for el_name, elements in new.items():
        if el_name not in source:
            source[el_name] = elements
        else:
            for html_elem, selectors in elements.items():
                if html_elem not in source[el_name]:
                    source[el_name][html_elem] = selectors


def _get_package_init(cur_module: str) -> ModuleType:

    def is_init(module_: Optional[ModuleType]) -> bool:
        return module_ is not None and getfile(module_).endswith('__init__.py')

    module_ = sys.modules.get(cur_module, None)

    if not is_init(module_):
        try:
            return sys.modules['.'.join(cur_module.split('.')[:-1])]
        except KeyError as kerr:
            raise InitNotFoundException('Unable to find __init__.py '
                                        f'for module {cur_module}') from kerr

    return cast(ModuleType, module_)


class BasePage:
    """
    This class is base for all PageObject.

    It will look in `SHAWl_YAML_PATH` for a ClassName.yaml file
    for all bases of initialized class. YAML file must have next structure:

    ::

        element_first_path_name:
          htmltag:
            selector: locator
          anotherhtmltag:
            selector: locator


    Selectors must be as in Selenium framework:

    * id
    * xpath
    * link text
    * partial link text
    * name
    * tag name
    * class name
    * css selector


    All attributes with BaseElement classes will be added while class
    is initializing.
    Attribute name will be `element_first_path_name_htmltag`.

    For adding new BaseElement attribute, `__init__` will look in
    `SHAWL_ELEMENTS_CLS_MODULE`
    (if there is no module - in module with this class) module for a class
    with name `HtmltagElement`. If class with this name not found,
    `BaseElement` will be used instead.
    """

    def __init__(self, driver: WebDriver):
        self._driver: WebDriver = driver
        self._page_strings: Dict[str, str] = dict()
        self._repr_name: str = self.__class__.__name__
        self._url_pattern: str = ''

        base_module: ModuleType = sys.modules.get(
            CONFIG.elements_classes_module,
            sys.modules[__name__])
        init_module: ModuleType = _get_package_init(self.__class__.__module__)
        all_elements: Dict[str, Dict[str, Any]] = dict()
        collections: Dict[str, Dict[str, Any]] = dict()
        buf_cls: type = self.__class__

        while buf_cls.__name__ != 'object':
            yaml_name: str = f'{buf_cls.__name__}.yaml'
            yaml_path: str = CONFIG.yaml_map.get(yaml_name,
                                                 CONFIG.source_yaml_path)
            cur_dict: Dict[str, Any] = _load_page(yaml_name, yaml_path)

            if buf_cls.__name__ == self.__class__.__name__:
                self._repr_name = cur_dict.pop('page_repr', self._repr_name)
                self._url_pattern = cur_dict.pop('url_pattern', '')

            _check_not_none_values(cur_dict, yaml_name)

            self._page_strings.update(
                cast(Dict[str, str], cur_dict.pop('page_strings', dict())))
            _merge_page_dicts(
                collections,
                cast(Dict[str, Any], cur_dict.pop('collections', dict())))
            _merge_page_dicts(
                all_elements,
                cur_dict)

            buf_cls, = buf_cls.__bases__

        for not_elem_key in ('page_repr', 'url_pattern', 'collections'):
            all_elements.pop(not_elem_key, None)

        self._init_elements(all_elements,
                            base_module,
                            init_module,
                            '{}Element',
                            BaseElement)
        self._init_elements(collections,
                            base_module,
                            init_module,
                            '{}Collection',
                            BaseCollection)

    def __str__(self) -> str:
        return (f'{self.__class__.__name__} elements: \n'
                + '\n'.join((f'- {k}' for k, v
                             in self.__dict__.items()
                             if not k.startswith('_')
                             and v is not None)))

    def __repr__(self) -> str:
        return self._repr_name

    def _init_elements(self,
                       yaml_part: Dict[str, Dict[str, Any]],
                       base_module: ModuleType,
                       init_module: Optional[ModuleType],
                       mask: str,
                       elem_init: type):
        # pylint:disable=too-many-arguments

        def get_class_for_init(html_elem: str) -> type:
            cls_name = mask.format(html_elem.capitalize())
            if (CONFIG.use_package_init_first
                    and hasattr(init_module, cls_name)):
                return cast(type, getattr(init_module, cls_name))
            try:
                return cast(type, getattr(base_module, cls_name))
            except AttributeError:
                return elem_init

        for el_name, elements in yaml_part.items():

            for html_elem, selectors in elements.items():
                repr_name: str = selectors.pop('repr', None)
                class_init: type = get_class_for_init(html_elem)
                element_obj: ShawlElems = class_init(self._driver,
                                                     repr_name=repr_name,
                                                     **selectors)
                setattr(self, f'{el_name}_{html_elem}', element_obj)

    @property
    def url_pattern(self) -> str:
        return self._url_pattern

    @property
    def driver(self) -> WebDriver:
        return self._driver

    @property
    def alert(self) -> Optional[Alert]:
        if self.alert_is_present():
            return Alert(self.driver)
        return None

    @property
    def page_strings(self) -> Dict[str, str]:
        return self._page_strings

    def switch_to_opened_tab(self,
                             old_handle: str,
                             elements_list: Optional[List[str]] = None,
                             page_name: Optional[str] = None):
        """
        Switch to first opened tab which is not - `old_handle`.

        After open new tab, current page will be validated
        with `validate_current_page` method.
        """
        for handle in self._driver.window_handles:
            if handle != old_handle:
                self._driver.switch_to.window(handle)
        self.validate_current_page(elements_list=elements_list,
                                   page_name=page_name)

    @check_server_error_after(log_level=CONFIG.log_level,
                              bad_msg=CONFIG.log_message)
    def switch_to_frame(self,
                        locator: Any,
                        wait: int = CONFIG.wait_timeout) -> bool:
        """
        Checking whether the given frame is available to switch to.
        If the frame is available it switches the given driver
        to the specified frame.
        Returns True if switched to frame, False otherwise
        """
        return wait_until(self._driver,
                          wait,
                          frame_to_be_available_and_switch_to_it(locator))

    @check_server_error_after(log_level=CONFIG.log_level,
                              bad_msg=CONFIG.log_message)
    def title_is(self, title: str, wait: int = CONFIG.wait_timeout) -> bool:
        """
        Check that page title equals expected.
        Method try to find if page title is an exact match with expected title
        during `wait` seconds.
        Returns True if the title matches, False otherwise
        """
        return wait_until(self._driver,
                          wait,
                          title_is(title))

    @check_server_error_after(log_level=CONFIG.log_level,
                              bad_msg=CONFIG.log_message)
    def title_contains(self,
                       title: str,
                       wait: int = CONFIG.wait_timeout) -> bool:
        """
        Check that page title contains expected.
        Method try to find if page title contains the expected title
        as substring during `wait` seconds.
        Returns True if the title matches, False otherwise
        """
        return wait_until(self._driver,
                          wait,
                          title_contains(title))

    @check_server_error_after(log_level=CONFIG.log_level,
                              bad_msg=CONFIG.log_message)
    def url_contains(self,
                     url: str,
                     wait: int = CONFIG.wait_timeout) -> bool:
        """
        Check that url contains a case-sensitive substring during 'wait'
        seconds.
        Returns True if the url matches, False otherwise
        """
        return wait_until(self._driver,
                          wait,
                          url_contains(url))

    @check_server_error_after(log_level=CONFIG.log_level,
                              bad_msg=CONFIG.log_message)
    def url_matches(self,
                    pattern: str,
                    wait: int = CONFIG.wait_timeout) -> bool:
        """
        Check that url is the exact match of the pattern during 'wait'
        seconds.
        Returns True if the url matches, False otherwise
        """
        return wait_until(self._driver,
                          wait,
                          url_matches(pattern))

    @check_server_error_after(log_level=CONFIG.log_level,
                              bad_msg=CONFIG.log_message)
    def url_to_be(self, url: str, wait: int = CONFIG.wait_timeout) -> bool:
        """
        Check that url is the exact match expected url during 'wait'
        seconds.
        Returns True if the url matches, False otherwise
        """
        return wait_until(self._driver,
                          wait,
                          url_to_be(url))

    @check_server_error_after(log_level=CONFIG.log_level,
                              bad_msg=CONFIG.log_message)
    def url_changes(self, url: str, wait: int = CONFIG.wait_timeout) -> bool:
        """
        Check that url is not matched to expected during 'wait'
        seconds.
        Returns True if the url is different, False otherwise
        """
        return wait_until(self._driver,
                          wait,
                          url_changes(url))

    @check_server_error_after(log_level=CONFIG.log_level,
                              bad_msg=CONFIG.log_message)
    def number_or_windows_to_be(self,
                                number: int,
                                wait: int = CONFIG.wait_timeout) -> bool:
        """
        Check that number of windows increased and new window is opened
        during 'wait' seconds.
        Returns True if there are `number` windows, False otherwise
        """
        return wait_until(self._driver,
                          wait,
                          new_window_is_opened(number))

    @check_server_error_after(log_level=CONFIG.log_level,
                              bad_msg=CONFIG.log_message)
    def new_window_is_opened(self,
                             number: int,
                             wait: int = CONFIG.wait_timeout) -> bool:
        """
        Check that number of windows is equal to specified value during 'wait'
        seconds.
        Returns True if new window was opened, False otherwise
        """
        return wait_until(self._driver,
                          wait,
                          number_of_windows_to_be(number))

    @check_server_error_after(log_level=CONFIG.log_level,
                              bad_msg=CONFIG.log_message)
    def alert_is_present(self, wait: int = CONFIG.wait_timeout) -> bool:
        """
        Check that an alert is present.
        Returns True if alert is present, False otherwise
        """
        return wait_until(self._driver,
                          wait,
                          alert_is_present())

    @check_server_error_after(log_level=CONFIG.log_level,
                              bad_msg=CONFIG.log_message)
    def validate_current_page(self,
                              elements_list: Optional[List[str]] = None,
                              page_name: Optional[str] = None,
                              url: Optional[str] = None,
                              validate_all: bool = False):
        """
        Validate current page. Method will validate that

        * all elements (current class attributes names) are on page;
        * page has `page_name` in title
        * current url is an `url`

        If keyword argument is not set, there won't be any validation,
        so you can get false-positive check, if will use method
        without keywords set.
        """

        def is_base_element(attr_val: Any) -> bool:
            return isinstance(attr_val, BaseElement)

        to_check: List[BaseElement] = list()

        if isinstance(elements_list, list) and elements_list:
            to_check.extend((v for k, v in self.__dict__.items()
                             if k in elements_list
                             and is_base_element(v)))
        elif validate_all and not elements_list:
            to_check.extend((v for k, v in self.__dict__.items()
                             if not k.startswith('_')
                             and is_base_element(v)))

        for elem in to_check:
            assert elem.is_present(), f'{elem} is not present'

        if page_name:
            assert page_name in self._driver.title, (f'"{page_name}" '
                                                     'is not in title '
                                                     f'"{self._driver.title}"')
        if url:
            assert self._driver.current_url == url, (
                'URL mismatch. \n'
                f'Expected: {url}\n'
                f'Actual: {self._driver.current_url}')

    @check_server_error_after(log_level=CONFIG.log_level,
                              bad_msg=CONFIG.log_message)
    def is_elements_invisible(self,
                              to_be_invisible: Union[List[str], str],
                              wait: int = CONFIG.wait_timeout) -> _INVISIBLE:
        """
        Returned NamedTuple has attributes `all_invisible: bool`
        and `not_invisible: List[str]`
        """
        result: List[str] = [
            element for element in _get_list(to_be_invisible)
            if not getattr(self, element).is_invisible(wait=wait)
            ]
        return _INVISIBLE(all_invisible=not bool(result), not_invisible=result)

    @check_server_error_after(log_level=CONFIG.log_level,
                              bad_msg=CONFIG.log_message)
    def is_elements_present(self,
                            to_be_present: Union[List[str], str],
                            wait: int = CONFIG.wait_timeout) -> _PRESENT:
        """
        Returned NamedTuple has attributes `all_present: bool`
        and `not_present: List[str]`
        """
        result: List[str] = [
            element for element in _get_list(to_be_present)
            if not getattr(self, element).is_present(wait=wait)
            ]
        return _PRESENT(all_present=not bool(result), not_present=result)

    @check_server_error_after(log_level=CONFIG.log_level,
                              bad_msg=CONFIG.log_message)
    def wait_to_page_load(self,
                          to_be_present: Union[List[str], str, None] = None,
                          to_be_invisible: Union[List[str], str, None] = None,
                          wait_present: int = CONFIG.wait_timeout,
                          wait_invisible: int = CONFIG.wait_timeout,
                          sleep_after: int = 0):
        # pylint:disable=too-many-arguments
        present: _PRESENT = self.is_elements_present(to_be_present,
                                                     wait=wait_present)
        invisible: _INVISIBLE = self.is_elements_invisible(to_be_invisible,
                                                           wait=wait_invisible)

        if not present.all_present or not invisible.all_invisible:
            raise AssertionError(
                'Page was not loaded properly! '
                f'Next items were not present {present.not_present}. '
                f'Next items were visible {invisible.not_invisible}.')

        # Known bug
        # https://bugs.chromium.org/p/chromedriver/issues/detail?id=3361
        if sleep_after > 0:
            sleep(sleep_after)


__all__ = ['BasePage']
