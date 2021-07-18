# -*- coding: utf-8 -*-
from typing import Iterator, List, Optional, Tuple

from selenium.common.exceptions import (
    StaleElementReferenceException,
    TimeoutException
)
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.expected_conditions import (
    presence_of_all_elements_located,
    visibility_of_all_elements_located,
    visibility_of_any_elements_located
)
from selenium.webdriver.support.wait import WebDriverWait

from ..config import SHAWL_CONFIG as CONFIG
from ..exceptions import NoSuchElementsException
from ..utils._waits import wait_until


class BaseCollection:
    """
    This class is base for all PageElement collections.

    This class is a wrap above list of WebElement.
    Property `collection` contains
    list of WebElement and provide lazy load of it.
    It will wait for any of WebElement to be present on the DOM for
    `SHAWL_LAZY_LOAD_TIMEOUT` seconds.

    Also, you can work with this class instance as with basic list.

    For example::


        base_collection = BaseCollection(driver, **{'css selector': 'div'})
        for element in base_collection:
            print(element.text)

        first_element = base_collection[0]

        assert len(base_collection) == 50
    """

    def __init__(self,
                 driver: WebDriver,
                 repr_name: Optional[str] = None,
                 **locators):
        self._driver: WebDriver = driver
        self._selector: Tuple[str, str] = list(locators.items())[0]
        self._collection: List[WebElement] = []
        self._repr_name: str = repr_name or (f'{self.__class__.__name__}: '
                                             f'{self._selector}')

    def __str__(self) -> str:
        return f'Selector: {self._selector}, Collection: {self._collection}'

    def __repr__(self) -> str:
        return self._repr_name

    def __len__(self) -> int:
        return len(self.collection)

    def __iter__(self) -> Iterator[WebElement]:
        return iter(self.collection)

    def __getitem__(self, item) -> WebElement:
        return self.collection[item]

    def __bool__(self) -> bool:
        return bool(self.collection)

    def _load(self):
        try:
            self._collection = WebDriverWait(
                self._driver,
                CONFIG.lazy_load_timeout
                ).until(presence_of_all_elements_located(self._selector))
        except TimeoutException as t_exc:
            raise NoSuchElementsException(
                'no such elements: '
                'Unable to locate elements: '
                '{"method":"%s","selector":"%s"}' % self._selector) from t_exc

    def _return_locator(self, selector_type: str) -> str:
        if self._selector[0] == selector_type:
            return self._selector[1]
        return ''

    @property
    def selector(self) -> Tuple[str, str]:
        return self._selector

    @property
    def id(self) -> str:
        # pylint: disable=invalid-name
        return self._return_locator('id')

    @property
    def xpath(self) -> str:
        return self._return_locator('xpath')

    @property
    def link_text(self) -> str:
        return self._return_locator('link text')

    @property
    def partial_link_text(self) -> str:
        return self._return_locator('partial link text')

    @property
    def name(self) -> str:
        return self._return_locator('name')

    @property
    def tag_name(self) -> str:
        return self._return_locator('tag name')

    @property
    def class_name(self) -> str:
        return self._return_locator('class name')

    @property
    def css_selector(self) -> str:
        return self._return_locator('css selector')

    @property
    def collection(self) -> List[WebElement]:
        if not self._collection or not isinstance(self._collection, list):
            self._load()
        try:
            for e in self._collection:
                isinstance(e.location, dict)
        except StaleElementReferenceException:
            self._load()
        return self._collection

    def any_is_visible(self, wait: int = CONFIG.wait_timeout) -> bool:
        """
        Check that at least one element from collection is visible
        on a web page during 'wait' seconds.
        Returns True if at least one element from collection is visible,
        False otherwise
        """
        return wait_until(self._driver,
                          wait,
                          visibility_of_any_elements_located(self._selector))

    def all_are_visible(self, wait: int = CONFIG.wait_timeout) -> bool:
        """
        Check that all elements from collection are present on the DOM of
        a page and visible during 'wait' seconds.
        Returns True if all elements from collection are visible,
        False otherwise
        """
        return wait_until(self._driver,
                          wait,
                          visibility_of_all_elements_located(self._selector))

    def any_is_present(self, wait: int = CONFIG.wait_timeout) -> bool:
        """
        Check that at least one element from collection is present
        on a web page during 'wait' seconds.
        Returns True if at least one element from collection is present,
        False otherwise
        """
        return wait_until(self._driver,
                          wait,
                          presence_of_all_elements_located(self._selector))


__all__ = ['BaseCollection']
