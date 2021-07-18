# -*- coding: utf-8 -*-
import importlib.util
import inspect
from os import walk
from os.path import isabs, join
from types import ModuleType
from typing import Any, Callable, Dict, Set, Tuple

import shawl

from ..config import SHAWL_CONFIG as CONFIG


def is_type_of(class_: type, type_: str) -> bool:
    if class_.__name__ != type_:
        buf_cls = class_
        while buf_cls.__name__ != 'object':
            if buf_cls.__name__ == type_:
                return True
            buf_cls, = buf_cls.__bases__
    return False


def path_to_module(path: str) -> str:
    return path.replace('/', '.').replace('\\', '.').replace('..', '.')


def get_module_name(obj_to_stub: Any) -> str:
    if inspect.isclass(obj_to_stub):
        attr_ = obj_to_stub.__name__
    else:
        attr_ = obj_to_stub.__class__.__name__

    if hasattr(shawl, attr_):
        return 'shawl'
    return str(obj_to_stub.__module__)


def get_func_declaration(fun_name: str, function_: Callable[..., Any]) -> str:
    buf_function = function_
    while '__wrapped__' in buf_function.__dict__:
        buf_function = buf_function.__dict__['__wrapped__']
    return f'def {fun_name}{inspect.signature(buf_function)}: ...'


def load_class(class_: type,
               is_elements: bool = False) -> Tuple[Dict[str, Set[str]],
                                                   Set[str]]:
    imports: Set[str] = set()
    attributes: Set[str] = set()
    methods: Set[str] = set()

    if not is_elements:
        page = class_('driver')
    else:
        page = class_('driver', **{'xpath': '//div'})

    for attr, attr_value in page.__dict__.items():
        if not callable(attr_value) and not attr.startswith('_'):
            imports.add(
                f'from {get_module_name(attr_value)} '
                f'import {attr_value.__class__.__name__}')
            attributes.add(
                f'    {attr} = None '
                f'# type: {attr_value.__class__.__name__}')
    for attr, attr_value in class_.__dict__.items():
        if callable(attr_value) and not attr.startswith('_'):
            methods.add(f'    {get_func_declaration(attr, attr_value)}')
    return {'methods': methods, 'attributes': attributes}, imports


def read_module(module_: ModuleType,
                cur_module: str) -> Tuple[Set[str],
                                          Set[str],
                                          Dict[type, Dict[str, Set[str]]]]:
    imports: Set[str] = set()
    functions: Set[str] = set()
    declared_classes: Dict[type, Dict[str, Set[str]]] = dict()

    for name, obj in inspect.getmembers(module_):
        if inspect.isfunction(obj) and obj.__module__ == cur_module:
            functions.add(get_func_declaration(name, obj))
        if inspect.isclass(obj):
            if obj.__module__ != cur_module:
                imports.add(f'from {get_module_name(obj)} import {name}')
                continue

            if is_type_of(obj, 'BasePage'):
                received_attrs, received_imports = load_class(obj)
            elif (is_type_of(obj, 'BaseElement')
                  or is_type_of(obj, 'BaseCollection')):
                received_attrs, received_imports = load_class(obj,
                                                              is_elements=True)
            else:
                continue
            declared_classes[obj] = received_attrs
            imports.update(received_imports)

    return imports, functions, declared_classes


def stub_file(dir_with_src: str, src: str):
    cur_module: str = path_to_module(dir_with_src)
    spec = importlib.util.spec_from_file_location(cur_module,
                                                  f'{dir_with_src}/{src}')
    buf_module = importlib.util.module_from_spec(spec)  # type: ignore
    spec.loader.exec_module(buf_module)  # type: ignore

    imports, functions, declared_classes = read_module(buf_module, cur_module)

    with open(f'{dir_with_src}/{src}i', 'w+', encoding='utf-8') as st_file:
        for import_ in imports:
            st_file.write(f'{import_}\n')
        st_file.write('\n\n')

        for function_ in functions:
            st_file.write(f'{function_}\n\n\n')

        for class_, attrs in declared_classes.items():
            if class_.__bases__[0] != 'object':  # type: ignore
                st_file.write(f'class {class_.__name__}'
                              f'({class_.__bases__[0].__name__}):\n')
            else:
                st_file.write(f'class {class_.__name__}:\n')

            if not any(attrs.values()):
                st_file.write('    pass\n')
                continue

            for attr in attrs.get('attributes', []):
                st_file.write(f'{attr}\n')

            st_file.write('\n')

            for method in attrs.get('methods', []):
                st_file.write(f'{method}\n\n')


def create_stubs(yaml_path: str, class_root_path: str):
    if isabs(class_root_path):
        raise ValueError('Class root path must be relative '
                         'to project root dir')

    importlib.import_module(path_to_module(class_root_path))

    if not isabs(yaml_path):
        yaml_path = join(CONFIG.project_root_path, yaml_path)

    class_root_path = join(CONFIG.project_root_path, class_root_path)

    for root_path, _, files in walk(yaml_path.replace(CONFIG.source_yaml_path,
                                                      class_root_path)):
        if '__pycache__' in root_path:
            continue
        for file in (f for f in files
                     if not f.endswith('.pyi') and f.endswith('.py')):
            stub_file(root_path, file)


__all__ = ['create_stubs']
