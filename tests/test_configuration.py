# -*- coding: utf-8 -*-
# pylint:disable=redefined-outer-name
# pylint:disable=protected-access
# pylint:disable=unused-argument
from os import environ, getcwd, mkdir, remove, rmdir
from os.path import join

import pytest

from shawl.config import SHAWL_CONFIG as CONFIG
from shawl.config import ShawlConfig, ShawlConfigError

CWD = getcwd()


@pytest.fixture()
def restore_defaults():
    yield
    CONFIG.project_root_path = CWD
    CONFIG.source_yaml_path = 'resources/dicts/pages'
    CONFIG.elements_classes_module = ''
    CONFIG.lazy_load_timeout = 5


@pytest.fixture()
def create_rc_file():
    mkdir('config_test')
    with open('.shawlrc', 'w+') as file:
        file.write(f'SHAWL_PROJECT_ROOT={CWD}\n')
        file.write('SHAWL_YAML_PATH=config_test\n')
        file.write('SHAWL_LAZY_LOAD_TIMEOUT=500\n')
        file.write('SHAWL_ELEMENTS_CLS_MODULE=shawl\n')
        file.write('SHAWL_USE_PACKAGE_INIT_FIRST=True\n')
    yield
    remove('.shawlrc')
    rmdir('config_test')
    environ['SHAWL_YAML_PATH'] = 'resources/dicts/pages'
    environ['SHAWL_LAZY_LOAD_TIMEOUT'] = '5'


@pytest.fixture()
def create_duplicated_yaml():
    yaml_path = 'resources/dicts/pages/subdir/CustomPage.yaml'
    with open(yaml_path, 'w+') as file:
        file.write(f'button: .div\n')
    yield
    remove(yaml_path)


def test_set_yaml_path(restore_defaults):
    path = 'resources'
    abs_path = join(getcwd(), path)
    CONFIG.source_yaml_path = path
    assert CONFIG.source_yaml_path == abs_path

    CONFIG._source_yaml_path = None
    CONFIG.source_yaml_path = abs_path
    assert CONFIG.source_yaml_path == abs_path

    CONFIG._source_yaml_path = None
    with pytest.raises(ShawlConfigError):
        CONFIG.source_yaml_path = 'path/file/not_exist'


def test_set_root_path(restore_defaults):
    path = 'resources'
    CONFIG.project_root_path = path
    assert CONFIG.project_root_path == path

    with pytest.raises(ShawlConfigError):
        CONFIG.project_root_path = 'resources/dicts/pages/CustomPage.yaml'

    CONFIG._project_root_path = None
    with pytest.raises(ShawlConfigError):
        CONFIG.project_root_path = 'path/file/not_exist'


def test_set_lazy_load_timeout(restore_defaults):
    CONFIG.lazy_load_timeout = 10
    assert CONFIG.lazy_load_timeout == 10

    with pytest.raises(ShawlConfigError):
        CONFIG._lazy_load_timeout = None
        CONFIG.lazy_load_timeout = 'None'

    with pytest.raises(ShawlConfigError):
        CONFIG.lazy_load_timeout = 0

    with pytest.raises(ShawlConfigError):
        CONFIG.lazy_load_timeout = -1


def test_set_classes_module(restore_defaults):
    module_ = 'shawl'
    CONFIG.elements_classes_module = module_
    assert CONFIG.elements_classes_module == module_

    CONFIG.elements_classes_module = 6
    assert CONFIG.elements_classes_module == module_

    CONFIG.elements_classes_module = 'None'
    with pytest.raises(ShawlConfigError):
        assert CONFIG.elements_classes_module

    CONFIG._elements_classes_module = None
    with pytest.raises(ShawlConfigError):
        assert not CONFIG.elements_classes_module


def test_load_config_from_rc_file(create_rc_file):
    new_conf = ShawlConfig()
    assert new_conf.project_root_path == CWD
    assert new_conf.source_yaml_path == join(CWD, 'config_test')
    assert new_conf.elements_classes_module == 'shawl'
    assert new_conf.use_package_init_first is True
    assert new_conf.lazy_load_timeout == 500


def test_duplicated_page(create_duplicated_yaml):
    new_conf = ShawlConfig()
    with pytest.raises(ShawlConfigError):
        assert new_conf.yaml_map


def test_yaml_map():
    root = CONFIG.source_yaml_path
    file_map = {
        'EmptyPageTwo.yaml': root,
        'CustomPage.yaml': root,
        'SubDir.yaml': join(root, 'subdir'),
        'SubSubDir.yaml': join(root, 'subdir', 'subsubdir')
        }
    new_conf = ShawlConfig()
    assert file_map == new_conf.yaml_map
