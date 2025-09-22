"""
Utilities for external dependencies and general helpers.
All imports here are external to the hired package.
"""

import json
from importlib.resources import files
import os
import urllib.request
from typing import Dict, Any


import yaml  # pip install PyYAML

proj_files = files('hired')
data_files = files('hired') / 'data'


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


# --------------------------------------------------------------------------------------
# Helpers

import importlib.resources
import os


def _merge_dicts(base: dict, override: dict) -> dict:
    """Merge two dicts shallowly, with override taking precedence."""
    result = base.copy()
    result.update(override)
    return result


def url_to_jdict(url: str) -> Dict[str, Any]:
    """
    Fetches JSON data from a given URL and returns it as a Python dictionary.

    Args:
        url: The URL of the JSON file.

    Returns:
        A dictionary representation of the JSON data.
    """
    try:
        with urllib.request.urlopen(url) as response:
            data = response.read().decode('utf-8')
            return json.loads(data)
    except Exception as e:
        print(f"Error fetching or parsing JSON from URL: {e}")
        return {}


# --------------------------------------------------------------------------------------
# Functions that manage resources

from pathlib import Path

schemas_files = data_files / 'schemas'
resume_jsons_files = data_files / 'resume_jsons'
resume_json_example = resume_jsons_files / 'test_resume.json'

DFLT_RESUME_SCHEMA_PATH = str(schemas_files / 'resume_schema.json')
DFLT_SCHEMA_URL = (
    "https://raw.githubusercontent.com/jsonresume/resume-schema/v1.0.0/schema.json"
)
DFLT_TEST_RESUME_URL = "https://raw.githubusercontent.com/jsonresume/resume-schema/refs/heads/v1.0.0/sample.resume.json"


def refresh_resume_schema():
    from ju import pydantic_model_to_code

    print('Get the schema (dict) from the url')
    new_schema = url_to_jdict(DFLT_SCHEMA_URL)
    print('Make pydantic models (code) from it')
    new_schema_code = pydantic_model_to_code(new_schema)
    print('Replace the code that is in resumejson_pydantic_models.py')
    (proj_files / 'resumejson_pydantic_models.py').write_text(
        f'"""Pydantic models for resume json schema\n"""\n{new_schema_code}'
    )

    print("Writing the schema in the schema file (for reference)...")
    Path(DFLT_RESUME_SCHEMA_PATH).write_text(json.dumps(new_schema))

    print('Refresh test json')
    Path(resume_json_example).write_text(json.dumps(url_to_jdict(DFLT_TEST_RESUME_URL)))


def jdict_to_pydantic_model(schema_jdict: Dict[str, Any]) -> str:
    """
    Transforms a JSON Schema dictionary into a Pydantic model string.

    This function requires the 'datamodel-code-generator' library.
    You can install it with:
    pip install 'datamodel-code-generator[http]'

    Args:
        schema_jdict: The JSON Schema as a Python dictionary.

    Returns:
        A string containing the generated Pydantic models.
    """
    try:
        from datamodel_code_generator import DataModelCodeGenerator, PythonVersion
        from datamodel_code_generator.parser.jsonschema import JsonSchemaParser

        # Create a parser instance with the JSON Schema data
        parser = JsonSchemaParser(
            json.dumps(schema_jdict),
            DataModelCodeGenerator,
            target_python_version=PythonVersion.PY_37,
        )

        # Generate the Python code (Pydantic models)
        return parser.parse()
    except ImportError:
        return "Error: The 'datamodel-code-generator' library is not installed. Please install it with: pip install 'datamodel-code-generator[http]'"
    except Exception as e:
        return f"Error transforming JSON Schema to Pydantic models: {e}"
