"""
Utilities for external dependencies and general helpers.
All imports here are external to the hired package.
"""

import json
from importlib.resources import files
import os
import urllib.request
from typing import Dict, Any, Mapping, Union
from hired.resumejson_pydantic_models import ResumeSchema

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


from typing import Union
from pydantic import ValidationError as PydanticValidationError
from jsonschema.exceptions import ValidationError as JsonSchemaValidationError

ValidationError = Union[PydanticValidationError, JsonSchemaValidationError]


def extract_friendly_errors(error_obj: ValidationError, schema=None, data=None):
    """
    Extracts a generator of user-friendly error messages from a validation error object.

    This function works with both Pydantic's ValidationError and jsonschema's
    ValidationError to provide a consistent output.

    Args:
        error_obj: The ValidationError instance to process.

    Yields:
        A tuple of (field, message) for each validation error.
    """
    if isinstance(error_obj, PydanticValidationError):
        for error in error_obj.errors():
            field = error['loc'][0]
            message = error['msg']
            yield field, message
    elif isinstance(error_obj, JsonSchemaValidationError):
        # The jsonschema.exceptions.ValidationError object might only represent the first error.
        # It's best to use jsonschema.iter_errors() to get all errors.
        # This requires the schema and data, which are not directly available in the exception object.
        # We'll handle the common case where a single error is passed in.
        # To get the full list, you would typically use jsonschema.iter_errors(schema, data).

        # This path extracts the field location from the error path tuple.
        field_path = list(error_obj.path)
        field = field_path[-1] if field_path else "root"
        yield field, error_obj.message


def validate_resume_content_dict(content: dict) -> dict:
    try:
        _ = ResumeSchema(**content)
    except Exception as e:
        for field, message in extract_friendly_errors(e):
            print(f"Error in field '{field}': {message}")
        raise
    return content


def ensure_resume_content_dict(content_src: Union[str, Mapping]) -> dict:
    """
    Get a schema-valid resume dict from various sources
    (json file, json string, dict, ...)
    """
    if isinstance(content_src, str):
        if os.path.exists(content_src):
            with open(content_src, 'r', encoding='utf-8') as f:
                content = json.load(f)
        else:
            try:
                content = json.loads(content_src)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON content provided: {e}")
    elif not isinstance(content, Mapping):
        raise TypeError(
            f"Content source must be a dict or a valid JSON string/filename: {content}"
        )
    return validate_resume_content_dict(content)


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
    import re

    def fix_anyurl_transform(code: str) -> str:
        """Transform generated code to replace AnyUrl with Optional[str] type alias"""

        # Note: The need for this egress comes from the fact that AnyUrl is too restrictive.
        #   By "too" restrictive, I mean, MORE restrictive than the json schema actually enforces.
        #   Using jsonschema (package) or pydantic.create_model, we get alignment (of schema version and example data).
        #   But when we use pydantic_model_to_code (which uses datamodel_code_generator)
        #   we get two failures:
        #      - Error in field 'basics': Input should be a valid URL, input is empty
        #      - Error in field 'projects': Input should be a valid URL, relative URL without a base
        # because of UrlAny that was created.

        # Check if AnyUrl is imported - if not, no changes needed
        if 'AnyUrl' not in code:
            return code

        # Remove AnyUrl from imports, handling various import patterns
        # Pattern 1: from pydantic import AnyUrl, ...
        code = re.sub(
            r'from pydantic import ([^,\n]*,\s*)?AnyUrl(,\s*[^,\n]*)?',
            r'from pydantic import \1\2',
            code,
        )

        # Pattern 2: from pydantic import ..., AnyUrl
        code = re.sub(
            r'(from pydantic import [^,\n]*),\s*AnyUrl\s*$',
            r'\1',
            code,
            flags=re.MULTILINE,
        )

        # Pattern 3: from pydantic import AnyUrl only
        code = re.sub(r'from pydantic import AnyUrl\n', '', code)

        # Clean up any leftover commas from import removal
        code = re.sub(r'from pydantic import\s*,', 'from pydantic import', code)
        code = re.sub(r',\s*,', ',', code)
        code = re.sub(r',\s*\)', ')', code)

        # Add the type alias definition after the imports
        lines = code.split('\n')
        import_end_idx = 0
        for i, line in enumerate(lines):
            if line.strip().startswith(
                ('from ', 'import ')
            ) and not line.strip().startswith('# '):
                import_end_idx = i

        # Insert the type alias after imports
        lines.insert(import_end_idx + 1, '')
        lines.insert(import_end_idx + 2, '# Type alias to avoid strict URL validation')
        lines.insert(import_end_idx + 3, 'AnyUrl = Optional[str]')
        lines.insert(import_end_idx + 4, '')

        return '\n'.join(lines)

    print('Get the schema (dict) from the url')
    new_schema = url_to_jdict(DFLT_SCHEMA_URL)
    print('Make pydantic models (code) from it')
    new_schema_code = pydantic_model_to_code(
        new_schema, egress_transform=fix_anyurl_transform
    )
    print('Replace the code that is in resumejson_pydantic_models.py')
    (proj_files / 'resumejson_pydantic_models.py').write_text(
        f'"""Pydantic models for resume json schema\n"""\n{new_schema_code}'
    )

    print("Writing the schema in the schema file (for reference)...")
    Path(DFLT_RESUME_SCHEMA_PATH).write_text(json.dumps(new_schema))

    print('Refresh test json')
    Path(resume_json_example).write_text(json.dumps(url_to_jdict(DFLT_TEST_RESUME_URL)))
