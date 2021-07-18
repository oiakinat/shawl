# -*- coding: utf-8 -*-
# pylint:disable=protected-access
from shawl import BaseCollection


def test_load_elements():
    b_collection = BaseCollection('driver', **{'xpath': '//div'})
    assert b_collection._collection == []
    assert b_collection.selector == ('xpath', '//div')


def test_check_str_repr():
    b_collection = BaseCollection('driver', **{'xpath': '//div'})
    str_ = ("Selector: ('xpath', '//div'), "
            'Collection: []')
    assert str(b_collection) == str_


def test_check_repr():
    b_collection = BaseCollection('driver', **{'xpath': '//div'})
    assert repr(b_collection) == "BaseCollection: ('xpath', '//div')"

    c_collection = BaseCollection('driver',
                                  repr_name='Test',
                                  **{'xpath': '//div'})
    assert repr(c_collection) == 'Test'
