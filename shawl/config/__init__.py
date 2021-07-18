# -*- coding: utf-8 -*-
import sys
from os import environ, getcwd, walk
from os.path import isabs, isdir, join
from typing import Dict, Union, cast

from dotenv import find_dotenv, load_dotenv

from . import _localization as steps_descr


class ShawlConfigError(Exception):
    pass


class ShawlConfig:
    """
    Config class for framework.
    """

    # pylint:disable=too-many-instance-attributes
    def __init__(self):
        self._rc_file: str = find_dotenv(filename='.shawlrc', usecwd=True)
        self._source_yaml_path: str = ''
        self._lazy_load_timeout: int = 0
        self._wait_timeout: int = 0
        self._project_root_path: str = ''
        self._elements_classes_module: str = ''
        self._use_package_init_first: bool = False
        self._use_allure: bool = True
        self._yaml_map: Dict[str, str] = dict()
        self._log_level: str = ''
        self._log_message: str = ''
        self._step_localization: str = ''
        if self._rc_file:
            load_dotenv(dotenv_path=self._rc_file)
        self.load_from_env()

    @property
    def yaml_map(self) -> Dict[str, str]:
        """
        Loaded map of yaml files for easier loading BasePages.
        """
        if not self._yaml_map:
            self._yaml_map = _get_yaml_files_path_dict(self.source_yaml_path)
        return self._yaml_map

    @property
    def source_yaml_path(self) -> str:
        """
        Path to yaml files with page description.
        Default value is 'resources/dicts/pages'
        """
        return self._source_yaml_path

    @source_yaml_path.setter
    def source_yaml_path(self, path: str):
        """
        Set path to yaml files with page description.
        """
        if not isabs(path):
            path = join(self.project_root_path, path)
        if isdir(path):
            self._source_yaml_path = path
        else:
            raise ShawlConfigError(
                'Unable to set source_yaml_path. '
                f'Check if "{path}" directory exists.')

    @property
    def lazy_load_timeout(self) -> int:
        """
        Time in seconds, how long to wait BaseElement.element to be present.
        Default value is 5.
        """
        return self._lazy_load_timeout

    @lazy_load_timeout.setter
    def lazy_load_timeout(self, timeout: int):
        """
        Set how long to wait BaseElement.element to be present.
        """
        if isinstance(timeout, int) and timeout > 0:
            self._lazy_load_timeout = timeout
        else:
            raise ShawlConfigError(
                'Unable to set lazy_load_timeout. '
                f'Check if "{timeout}" valid value.')

    @property
    def step_localization(self) -> str:
        """
        Step description localization.
        Possible values: RU, EN.
        Default value is EN.
        """
        return self._step_localization

    @step_localization.setter
    def step_localization(self, language: str):
        """
        Set step description localization.
        """
        if isinstance(language, str) and language:
            self._step_localization = language

    @property
    def custom_step_description(self) -> Dict[str, str]:
        """
        Custom step description.
        If custom step description was not added, empty dict will be returned.
        """
        return cast(Dict[str, str], getattr(steps_descr, 'CUSTOM', dict()))

    @custom_step_description.setter
    def custom_step_description(self, step_description: Dict[str, str]):
        """
        Set custom step description.
        Also step_localization will be set to CUSTOM.
        """
        if isinstance(step_description, dict) and step_description:
            self.step_localization = 'CUSTOM'
            setattr(steps_descr, self.step_localization, step_description)

    @property
    def step_description(self) -> Dict[str, str]:
        """
        Step description according to current step_localization.
        """
        return cast(
            Dict[str, str],
            getattr(steps_descr, self._step_localization, steps_descr.EN))

    @property
    def wait_timeout(self) -> int:
        """
        Time in seconds, how long to wait during waiter methods.
        Default value is 5.
        """
        return self._wait_timeout

    @wait_timeout.setter
    def wait_timeout(self, timeout: int):
        """
        Set how long to wait during waiter methods.
        """
        if isinstance(timeout, int) and timeout > 0:
            self._wait_timeout = timeout
        else:
            raise ShawlConfigError(
                'Unable to set wait_timeout. '
                f'Check if "{timeout}" valid value.')

    @property
    def project_root_path(self) -> str:
        """
        Your project root path.
        Default value is current working dir.
        """
        return self._project_root_path

    @project_root_path.setter
    def project_root_path(self, path: str):
        """
        Set your project root path.
        """
        if isdir(path):
            self._project_root_path = path
        else:
            raise ShawlConfigError(
                'Unable to set project_root_path. '
                f'Check if "{path}" directory exists.')

    @property
    def elements_classes_module(self) -> str:
        """
        Your module with BaseElements classes.
        Must be as in `sys.modules` keys.
        Default value is empty.
        """
        if (self._elements_classes_module != 'default'
                and self._elements_classes_module not in sys.modules):
            raise ShawlConfigError(
                f'Unable to load "{self._elements_classes_module}" module. '
                'Check if this module was already imported and loaded.')
        return self._elements_classes_module

    @elements_classes_module.setter
    def elements_classes_module(self, module: str):
        """
        Set your module with BaseElements classes.
        """
        if isinstance(module, str):
            self._elements_classes_module = module

    @property
    def use_package_init_first(self) -> bool:
        """
        Option to try to find BaseElements classes
        in __init__.py of BasePage class
        module first. Must be boolean.
        Default value is False.
        """
        return self._use_package_init_first

    @use_package_init_first.setter
    def use_package_init_first(self, value: Union[bool, str]):
        """
        Set if try to find BaseElements classes
        in __init__.py of BasePage class module first
        """
        if isinstance(value, bool):
            self._use_package_init_first = value
        else:
            self._use_package_init_first = str(value).lower() == 'true'

    @property
    def use_allure(self) -> bool:
        """
        Option to wrap captured selenium WebElement methods with allure steps.
        """
        return self._use_allure

    @use_allure.setter
    def use_allure(self, value: Union[bool, str]):
        """
        Set if to wrap captured selenium WebElement methods with allure steps.
        """
        if isinstance(value, bool):
            self._use_allure = value
        else:
            self._use_allure = str(value).lower() == 'true'

    @property
    def log_level(self) -> str:
        """
        Log level for check_server_error_after using across the framework.
        Default value is 'SEVERE'.
        """
        return self._log_level

    @log_level.setter
    def log_level(self, value: str):
        """
        Set log level for check_server_error_after using across the framework.
        """
        if isinstance(value, str):
            self._log_level = value

    @property
    def log_message(self) -> str:
        """
        Log message for check_server_error_after using across the framework.
        Default value is '500 (Internal Server Error)'.
        """
        return self._log_message

    @log_message.setter
    def log_message(self, value: str):
        """
        Set log message for check_server_error_after
        using across the framework.
        """
        if isinstance(value, str):
            self._log_message = value

    def load_from_env(self):
        """
        Method will set for properties values from system environment,
        or set default values.
        """
        self.project_root_path = environ.get(
            'SHAWL_PROJECT_ROOT', getcwd())
        self.source_yaml_path = environ.get(
            'SHAWL_YAML_PATH', 'resources/dicts/pages')
        self.lazy_load_timeout = int(environ.get(
            'SHAWL_LAZY_LOAD_TIMEOUT', 5))
        self.wait_timeout = int(environ.get(
            'SHAWL_WAIT_TIMEOUT', 5))
        self.elements_classes_module = environ.get(
            'SHAWL_ELEMENTS_CLS_MODULE', 'default')
        self.use_package_init_first = environ.get(
            'SHAWL_USE_PACKAGE_INIT_FIRST', False)  # type: ignore
        self.use_allure = environ.get(
            'SHAWL_USE_ALLURE', True)  # type: ignore
        self.log_level = environ.get(
            'SHAWL_LOG_LEVEL_TO_FAIL_ON', 'SEVERE')
        self.log_message = environ.get(
            'SHAWL_LOG_MESSAGE_TO_FAIL_ON', '500 (Internal Server Error)')
        self.step_localization = environ.get(
            'SHAWL_STEP_LOCALIZATION', 'EN')


def _get_yaml_files_path_dict(yaml_path: str) -> Dict[str, str]:
    result: Dict[str, str] = dict()
    for root, _, files in walk(yaml_path):
        for file in files:
            if file in result:
                raise ShawlConfigError(
                    f'Duplicated file "{join(yaml_path, root, file)}" found. '
                    'Current version of framework does not support '
                    'class names or .yaml file names duplication')
            result[file] = join(yaml_path, root)
    return result


SHAWL_CONFIG = ShawlConfig()

__all__ = ['SHAWL_CONFIG']
