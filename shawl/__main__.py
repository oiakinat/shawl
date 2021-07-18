# -*- coding: utf-8 -*-
import argparse

from shawl.utils import create_stubs


def parse_arguments():
    parser = argparse.ArgumentParser(
        description='Shawl: YAML powered Selenium wrapper')
    parser.add_argument(
        'yaml_path',
        type=str,
        help='Path to yaml files',
        default=None
        )
    parser.add_argument(
        'class_root_path',
        type=str,
        help='Path to root module with classes',
        default=None
        )
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_arguments()
    create_stubs(args.yaml_path, args.class_root_path)
