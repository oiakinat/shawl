# -*- coding: utf-8 -*-
# pylint: disable=too-many-public-methods
from time import sleep
from typing import Any, Optional, Tuple

from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.expected_conditions import (
    element_located_selection_state_to_be,
    element_located_to_be_selected,
    element_to_be_clickable,
    invisibility_of_element_located,
    presence_of_element_located,
    staleness_of,
    text_to_be_present_in_element,
    text_to_be_present_in_element_value,
    visibility_of_element_located
)
from selenium.webdriver.support.wait import WebDriverWait

from ..config import SHAWL_CONFIG as CONFIG
from ..utils._allure_utils import callable_with_allure
from ..utils._waits import wait_until


class BaseElement:
    """
    This class is base for all PageElement.

    This class is a wrap above WebElement. Property `element` contains
    instance of WebElement and provide lazy load of this instance.
    It will wait for a WebElement to be present on the DOM for
    `SHAWL_LAZY_LOAD_TIMEOUT` seconds.

    Also, you can call any of WebElement attribute just from BaseElement
    instance, there is no need to implement any wraps above them.

    For example::


        base_element = BaseElement(driver, **{'css selector': 'div'})
        base_element.find_element_by_css_selector('.class')
        print(base_element.text)

    All WebElement will be wrapped into a function with @allure.step()
    decorator with default description, stored in `ALLURE_STEP_MAP`,
    you can override any of default description if you wish.

    Be careful, this feature won't work if you override any of
    WebElement attribute. If you will need to call WebElement attribute then -
    use `element` property.

    Example::

        class TextElement(BaseElement):
            def click(self):
                print('Nope')
                self._driver.quit()


        text_element = TextElement(driver, **{'css selector': 'div'})
        text_element.element.click() # WebElement instance will be clicked
        text_element.click() # 'Nope' will be printed and driver destroyed
    """

    def __init__(self,
                 driver: WebDriver,
                 repr_name: Optional[str] = None,
                 **locators):
        self._driver: WebDriver = driver
        self._selector: Tuple[str, str] = list(locators.items())[0]
        self._element: WebElement = None
        self._repr_name: str = repr_name or (f'{self.__class__.__name__}: '
                                             f'{self._selector}')

    def __getattr__(self, item: str) -> Any:
        # This magic method will be invoked if current class has no item.

        # Try to get item from Selenium object
        attr = getattr(self.element, item)
        # If success and has cofig to use Allure,
        # wrap it into Allure annotated step function
        # and return it. Otherwise just return Selenium WebElement item
        if callable(attr) and CONFIG.use_allure:
            return callable_with_allure(item, self._repr_name, attr)

        return attr

    def __str__(self) -> str:
        return f'Selector: {self._selector}, Element: {self._element}'

    def __repr__(self) -> str:
        return self._repr_name

    def _load(self):
        self._element = WebDriverWait(
            self._driver,
            CONFIG.lazy_load_timeout
            ).until(presence_of_element_located(self._selector))

    def _return_locator(self, selector_type: str) -> str:
        if self._selector[0] == selector_type:
            return self._selector[1]
        return ''

    @property
    def selector(self) -> Tuple[str, str]:
        return self._selector

    @property
    def element(self) -> WebElement:
        if self._element is None or not isinstance(self._element, WebElement):
            self._load()
        try:
            # We have one bad place on UI, where StaleElementReferenceException
            # raised right after this operation in any WebElement called method
            # So this ugly fix is must have, because even implicit waits can't
            # help us to avoid sudden StaleElementReferenceException
            self._element.is_enabled()
            isinstance(self._element.location, dict)
        except StaleElementReferenceException:
            self._load()
        return self._element

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

    def is_present(self, wait: int = CONFIG.wait_timeout) -> bool:
        """
        Check that element is present during 'wait' seconds.
        Returns True if element is present, False otherwise
        """
        return wait_until(self._driver,
                          wait,
                          presence_of_element_located(self._selector))

    def is_invisible(self, wait: int = CONFIG.wait_timeout) -> bool:
        """
        Check that element is invisible during 'wait' seconds.
        Returns True if element is invisible, False otherwise
        """
        return wait_until(self._driver,
                          wait,
                          invisibility_of_element_located(self._selector))

    def is_visible(self, wait: int = CONFIG.wait_timeout) -> bool:
        """
        Check that element is visible during 'wait' seconds.
        Returns True if element is visible, False otherwise
        """
        return wait_until(self._driver,
                          wait,
                          visibility_of_element_located(self._selector))

    def is_clickable(self, wait: int = CONFIG.wait_timeout) -> bool:
        """
        Check that element is clickable during 'wait' seconds.
        Returns True if element is clickable, False otherwise
        """
        return wait_until(self._driver,
                          wait,
                          element_to_be_clickable(self._selector))

    def is_stale(self, wait: int = CONFIG.wait_timeout) -> bool:
        """
        Check that element is no longer attached to the DOM
        during 'wait' seconds.
        Returns True if element is stale, False otherwise
        """
        return wait_until(self._driver,
                          wait,
                          staleness_of(self.element))

    def is_selected(self, wait: int = CONFIG.wait_timeout) -> bool:
        """
        Check that element is selected during 'wait' seconds.
        Returns True if element is selected, False otherwise
        """
        return wait_until(self._driver,
                          wait,
                          element_located_to_be_selected(self._selector))

    def is_in_selection_state(self,
                              state: bool,
                              wait: int = CONFIG.wait_timeout) -> bool:
        """
        Check that element state is selected or not during 'wait' seconds.
        Returns True if selected state is `is_selected`, False otherwise
        """
        return wait_until(self._driver,
                          wait,
                          element_located_selection_state_to_be(self._selector,
                                                                state))

    def has_text_in_value(self,
                          text: str,
                          wait: int = CONFIG.wait_timeout) -> bool:
        """
        Check that given text is present in the element's 'value' attribute
        during 'wait' seconds.
        Returns True if text is present in value, false otherwise.
        """
        return wait_until(self._driver,
                          wait,
                          text_to_be_present_in_element_value(self._selector,
                                                              text))

    def has_text(self, text: str, wait: int = CONFIG.wait_timeout) -> bool:
        """
        Check that given text is present in the specified element
        during 'wait' seconds.
        Returns True if text is present, false otherwise.
        """
        return wait_until(self._driver,
                          wait,
                          text_to_be_present_in_element(self._selector, text))

    def blinked(self, wait: int = CONFIG.lazy_load_timeout) -> bool:
        """
        Check that element fist was present and than disappeared
        during 'wait' seconds.
        Returns True if element blinked, false otherwise.
        """
        sleep(0.5)
        return self.is_present(wait=wait) and self.is_invisible(wait=wait)

    def scroll_to(self) -> WebElement:
        location = self.element.location
        self._driver.execute_script(f'window.scrollTo({location.get("x")},'
                                    f'{location.get("y") - 150})')
        return self.element

    def clear_via_backspace(self):
        self.element.send_keys(Keys.CONTROL, Keys.BACKSPACE)


__all__ = ['BaseElement']
