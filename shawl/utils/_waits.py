# -*- coding: utf-8 -*-
from contextlib import suppress
from typing import Any, Callable

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.wait import WebDriverWait


def wait_until(driver: WebDriver,
               wait: int,
               method: Callable[..., Any]) -> bool:
    with suppress(Exception):
        return bool(WebDriverWait(driver, wait).until(method))
    return False


__all__ = ['wait_until']
