# -*- coding: utf-8 -*-
# pylint:disable=protected-access
# pylint:disable=redefined-outer-name
# pylint:disable=unused-argument
# pylint:disable=wrong-import-order
from os import remove

import pytest

import tests.elements as init
from shawl import BaseCollection, BaseElement, BasePage
from shawl.config import SHAWL_CONFIG as CONFIG
from shawl.core._base_page import _check_not_none_values, _merge_page_dicts
from shawl.exceptions import NoneValuesInYamlException
from tests.elements.elements import (
    ButtonElement,
    DivCollection,
    InputElement,
    LiCollection
)
from tests.elements.pages import CustomPage


@pytest.fixture()
def create_yaml_file():
    file_name = f'{CONFIG.source_yaml_path}/ParentPage.yaml'
    with open(file_name, 'w+') as file:
        file.write('search:\n')
        file.write('  input:\n')
        file.write('    class: .input_homepage')
    yield
    remove(file_name)


@pytest.fixture()
def create_yaml_file_with_url():
    file_name = f'{CONFIG.source_yaml_path}/UrlPage.yaml'
    with open(file_name, 'w+') as file:
        file.write('url_pattern: "http://{}/one/two/three"\n')
    yield
    remove(file_name)


def test_check_none():
    dict_one = {
        'search': None,
        'textbox': {
            'div': {
                'id': 'some_id'
                }
            }
        }
    dict_two = {
        'search': {
            'div': None,
            'input': {
                'css': 'input_css'
                }
            },
        'textbox': {
            'div': {
                'id': 'some_id'
                }
            }
        }
    dict_three = {
        'search': {
            'div': {
                'id': None
                },
            'input': {
                'css': 'input_css'
                }
            },
        'textbox': {
            'div': {
                'id': 'some_id'
                }
            }
        }
    dict_four = {
        'search': {
            'div': {
                'id': 'some_id'
                }
            },
        'collections': None
        }

    with pytest.raises(NoneValuesInYamlException):
        _check_not_none_values(dict_one, 'BasePage.yaml')

    with pytest.raises(NoneValuesInYamlException):
        _check_not_none_values(dict_two, 'BasePage.yaml')

    with pytest.raises(NoneValuesInYamlException):
        _check_not_none_values(dict_three, 'BasePage.yaml')

    with pytest.raises(NoneValuesInYamlException):
        _check_not_none_values(dict_four, 'BasePage.yaml')


def test_check_merge_dicts():
    dict_one = {
        'search': {
            'div': {
                'id': 'some_id',
                'css': 'some_css'
                },
            'input': {
                'css': 'input_css'
                }
            },
        'textbox': {
            'div': {
                'id': 'some_id'
                }
            }
        }

    dict_two = {
        'search': {
            'div': {
                'id': 'another_id',
                'css': 'another_css'
                },
            'li': {
                'css': 'li_css'
                }
            },
        'textbox': {
            'div': {
                'id': 'another_id'
                },
            'a': {
                'link': 'link'
                }
            },
        'important': {
            'h1': {
                'id': 'another_id'
                }
            }
        }

    _merge_page_dicts(dict_one, dict_two)
    assert dict_one == {
        'search': {
            'div': {
                'id': 'some_id',
                'css': 'some_css'
                },
            'input': {
                'css': 'input_css'
                },
            'li': {
                'css': 'li_css'
                }
            },
        'textbox': {
            'div': {
                'id': 'some_id'
                },
            'a': {
                'link': 'link'
                }
            },
        'important': {
            'h1': {
                'id': 'another_id'
                }
            }
        }


def test_load_page_without_elements_impl():
    CONFIG.source_yaml_path = 'resources/dicts/pages'
    c_page = CustomPage('driver')
    for attr in ('search_input', 'search_button', 'web_tab_a', 'map_tab_a'):
        assert hasattr(c_page, attr)
        assert isinstance(getattr(c_page, attr), BaseElement)
    for attr in ('all_div', 'all_li', 'many_a'):
        assert hasattr(c_page, attr)
        assert isinstance(getattr(c_page, attr), BaseCollection)
    assert c_page.page_strings == {
        'locator_pattern': '//div//%s',
        'title_text': 'Hello there'
        }


def test_load_page_with_elements_impl():
    CONFIG.source_yaml_path = 'resources/dicts/pages'
    CONFIG.elements_classes_module = 'tests.elements.elements'
    c_page = CustomPage('driver')
    for attr, class_ in (('search_input', InputElement),
                         ('search_button', ButtonElement),
                         ('web_tab_a', BaseElement),
                         ('map_tab_a', BaseElement)):
        assert hasattr(c_page, attr)
        assert isinstance(getattr(c_page, attr), class_)
    for attr, class_ in (('all_div', DivCollection),
                         ('all_li', LiCollection),
                         ('many_a', BaseCollection)):
        assert hasattr(c_page, attr)
        assert isinstance(getattr(c_page, attr), BaseCollection)
    assert c_page.page_strings == {
        'locator_pattern': '//div//%s',
        'title_text': 'Hello there'
        }


def test_load_page_with_elements_impl_init_first():
    CONFIG.source_yaml_path = 'resources/dicts/pages'
    CONFIG.elements_classes_module = 'tests.elements.elements'
    CONFIG.use_package_init_first = True
    c_page = CustomPage('driver')
    for attr, class_ in (('search_input', init.InputElement),
                         ('search_button', ButtonElement),
                         ('web_tab_a', BaseElement),
                         ('map_tab_a', BaseElement)):
        assert hasattr(c_page, attr)
        assert isinstance(getattr(c_page, attr), class_)
    for attr, class_ in (('all_div', init.DivCollection),
                         ('all_li', LiCollection),
                         ('many_a', BaseCollection)):
        assert hasattr(c_page, attr)
        assert isinstance(getattr(c_page, attr), BaseCollection)
    assert hasattr(c_page.search_input, 'only_for_init')
    assert hasattr(c_page.all_div, 'only_for_init')

    CONFIG.use_package_init_first = False
    c_page = CustomPage('driver')
    assert 'only_for_init' not in c_page.search_input.__dict__
    assert 'only_for_init' not in c_page.all_div.__dict__


def test_load_parent_element(create_yaml_file):
    class ParentPage(CustomPage):
        pass

    p_page = ParentPage('driver')
    assert p_page.search_input._selector == ('class', '.input_homepage')


def test_load_url(create_yaml_file_with_url):
    class UrlPage(CustomPage):
        domain = 'google.com'

    u_page = UrlPage('driver')
    assert u_page.url_pattern.format(
        u_page.domain) == 'http://google.com/one/two/three'


def test_create_instance_without_elements():
    class EmptyPage(BasePage):
        pass

    class EmptyPageTwo(BasePage):
        pass

    e_page = EmptyPage('driver')
    assert not [k for k, v
                in e_page.__dict__.items()
                if not callable(v)
                and not k.startswith('_')
                and k != '_driver'
                and v]

    e_page_two = EmptyPageTwo('driver')
    assert not [k for k, v
                in e_page_two.__dict__.items()
                if not callable(v)
                and not k.startswith('_')
                and k != '_driver'
                and v]


def test_check_str_repr():
    c_page = CustomPage('driver')
    str_ = ('CustomPage elements: \n'
            '- search_input\n'
            '- search_button\n'
            '- web_tab_a\n'
            '- map_tab_a\n'
            '- all_div\n'
            '- all_li\n'
            '- many_a')
    assert str(c_page) == str_


def test_check_repr():
    class EmptyPage(BasePage):
        pass

    class EmptyPageTwo(EmptyPage):
        pass

    c_page = CustomPage('driver')
    assert repr(c_page) == 'Page description'

    ep_two = EmptyPageTwo('driver')
    assert repr(ep_two) == 'EmptyPageTwo'


def test_check_driver_prop():
    c_page = CustomPage('driver')
    assert c_page.driver == 'driver'


def test_load_elements():
    b_element = BaseElement('driver', **{'xpath': '//div'})
    assert b_element._element is None
    assert b_element.selector == ('xpath', '//div')
