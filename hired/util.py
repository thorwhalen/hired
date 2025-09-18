"""
Utilities for external dependencies and general helpers.
All imports here are external to the hired package.
"""

import json
from typing import Any
from importlib.resources import files
import os


proj_files = files('hired')


def _load_json_file(path: str) -> dict:
    """Load a JSON file from the given path."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


# YAML and TOML are optional; import if available
try:
    import yaml

    def _load_yaml_file(path: str) -> dict:
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

except ImportError:

    def _load_yaml_file(path: str) -> dict:
        raise ImportError('PyYAML is required for YAML support')


try:
    import toml

    def _load_toml_file(path: str) -> dict:
        with open(path, 'r', encoding='utf-8') as f:
            return toml.load(f)

except ImportError:

    def _load_toml_file(path: str) -> dict:
        raise ImportError('toml is required for TOML support')


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
