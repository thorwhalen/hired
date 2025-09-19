"""
Utilities for external dependencies and general helpers.
All imports here are external to the hired package.
"""

import json
from typing import Any
from importlib.resources import files
import os

import yaml  # pip install PyYAML

proj_files = files('hired')


def _load_json_file(path: str) -> dict:
    """Load a JSON file from the given path."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


try:
    import toml

    def _load_toml_file(path: str) -> dict:
        with open(path, 'r', encoding='utf-8') as f:
            return toml.load(f)

except ImportError:

    def _load_toml_file(path: str) -> dict:
        raise ImportError('toml is required for TOML support')


def load_yaml(yaml_path: str):
    """
    Loads a YAML file using PyYAML.
    This works in Python 3.7+ because dicts preserve insertion order.
    """
    with open(yaml_path, 'r') as file:
        # Use safe_load for security reasons.
        return yaml.safe_load(file)


def dump_yaml(d: dict, yaml_path: str):
    """
    Dumps a dictionary to a YAML file using PyYAML,
    preserving key order and using a readable block style.
    """
    with open(yaml_path, 'w') as file:
        # sort_keys=False is crucial to prevent alphabetical sorting.
        # default_flow_style=False ensures a readable, multi-line format.
        yaml.dump(d, file, sort_keys=False, default_flow_style=False)


import importlib.resources
import os


def _get_package_data_path(relative_path: str) -> str:
    """Resolve a path to a data file within the package."""
    # This is a simple version; for real packages, use importlib.resources.files
    base = os.path.dirname(__file__)
    return os.path.join(base, 'data', relative_path)


def _merge_dicts(base: dict, override: dict) -> dict:
    """Merge two dicts shallowly, with override taking precedence."""
    result = base.copy()
    result.update(override)
    return result
