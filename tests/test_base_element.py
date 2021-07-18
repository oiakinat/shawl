# -*- coding: utf-8 -*-
# pylint:disable=protected-access
from shawl import BaseElement


def test_load_elements():
    b_element = BaseElement('driver', **{'xpath': '//div'})
    assert b_element._element is None
    assert b_element._selector == ('xpath', '//div')


def test_check_str_repr():
    b_element = BaseElement('driver', **{'xpath': '//div'})
    str_ = ("Selector: ('xpath', '//div'), "
            'Element: None')
    assert str(b_element) == str_


def test_check_repr():
    b_element = BaseElement('driver', **{'xpath': '//div'})
    assert repr(b_element) == "BaseElement: ('xpath', '//div')"

    c_element = BaseElement('driver', repr_name='Test', **{'xpath': '//div'})
    assert repr(c_element) == 'Test'
