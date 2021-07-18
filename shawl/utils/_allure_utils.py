# -*- coding: utf-8 -*-
from typing import Any, Callable

from allure_commons._allure import StepContext
from allure_commons.utils import func_parameters

from ..config import SHAWL_CONFIG as CONFIG


def callable_with_allure(item_name: str,
                         repr_name: str,
                         callable_: Callable[..., Any]) -> Callable[..., Any]:
    default_title: str = CONFIG.step_description['default_title']
    title_pattern: str = CONFIG.step_description.get(item_name, default_title)

    def wrap_for_allure(*args, **kwargs):
        if item_name == 'send_keys':
            title = title_pattern.format(repr_name, text=args)
        else:
            title = title_pattern.format(repr_name, *args, **kwargs)
        with StepContext(title, func_parameters(callable_, *args, **kwargs)):
            return callable_(*args, **kwargs)

    return wrap_for_allure


__all__ = ['callable_with_allure']
