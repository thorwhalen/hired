"""
Utilities for external dependencies and general helpers.
All imports here are external to the hired package.
"""

import json
from importlib.resources import files
import os
from typing import Mapping, Union
from pathlib import Path

import yaml  # pip install PyYAML

from hired._converters import ensure_dict
from hired.resumejson_pydantic_models import ResumeSchema

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
from pydantic import ValidationError as PydanticValidationError
from jsonschema.exceptions import ValidationError as JsonSchemaValidationError


def _merge_dicts(base: dict, override: dict) -> dict:
    """Merge two dicts shallowly, with override taking precedence."""
    result = base.copy()
    result.update(override)
    return result


ValidationErrorType = Union[PydanticValidationError, JsonSchemaValidationError]
ValidationErrors = (PydanticValidationError, JsonSchemaValidationError)
JsonContentStr = str  # JSON string
PathStr = str  # filesystem path
ResumeSource = Union[PathStr, JsonContentStr, Path, Mapping]
ResumeDict = dict  # one that is valid in the ResumeSchema sense


def extract_friendly_errors(error_obj: ValidationErrorType, schema=None, data=None):
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


def validation_friendly_errors_string(
    error_obj: ValidationErrorType,
    schema=None,
    data=None,
) -> str:
    return '\n'.join(
        f"Error in field '{field}': {message}"
        for field, message in extract_friendly_errors(error_obj, schema, data)
    )


def ensure_resume_content_dict(content_src: ResumeSource) -> ResumeDict:
    """
    Get a schema-valid resume dict from various sources
    (json file, json string, dict, ...)
    """
    if isinstance(content_src, Path):
        content_src = str(content_src.expanduser())
    if isinstance(content_src, str):
        if os.path.exists(content_src):
            with open(content_src, 'r', encoding='utf-8') as f:
                content = json.load(f)
        else:
            try:
                content = json.loads(content_src)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON content provided: {e}")
    elif not isinstance(content_src, Mapping):
        raise TypeError(
            f"Content source must be a dict or a valid JSON string/filename: {content_src}"
        )
    return validate_resume_content_dict(content)


def _prune_none(obj):
    """Recursively remove keys or list items that are None so schema validation doesn't see explicit nulls for optional fields."""
    if isinstance(obj, dict):
        return {k: _prune_none(v) for k, v in obj.items() if v is not None}
    if isinstance(obj, list):
        return [_prune_none(x) for x in obj if x is not None]
    return obj


def normalize_and_validate_resume(raw: Mapping, *, strict: bool = True):
    """Normalize and validate a resume-like mapping.

    - Prunes None values.
    - Validates via Pydantic ResumeSchemaExtended (allows extra fields).
    - If strict is True and jsonschema is available, will attempt schema
      validation against the packaged JSON schema (best-effort).

    Returns a ResumeSchemaExtended instance on success. Raises
    pydantic.ValidationError on failure.
    """
    from hired.base import ResumeSchemaExtended

    # Make a shallow dict to ensure we mutate a copy
    if not isinstance(raw, Mapping):
        raise TypeError('raw must be a mapping')

    pruned = _prune_none(dict(raw))

    # First, construct the pydantic model (this provides strong typing)
    model = ResumeSchemaExtended(**pruned)

    # Optionally perform jsonschema validation if the package schema exists
    if strict:
        try:
            import jsonschema

            schema_path = DFLT_RESUME_SCHEMA_PATH
            try:
                schema = _load_json_file(schema_path)
            except FileNotFoundError:
                schema = None

            if schema is not None:
                # Will raise jsonschema.ValidationError if invalid
                jsonschema.validate(instance=pruned, schema=schema)
        except ImportError:
            # jsonschema not available — skip schema validation
            pass

    return model


def get_jsonschema_errors(
    content: Mapping, schema_path: str | None = None
) -> list[str]:
    """Return a list of jsonschema validation error messages for the content.

    If jsonschema is not available or the schema file is missing, returns an
    empty list.
    """
    try:
        import jsonschema
    except ImportError:
        return []

    try:
        schema_path = schema_path or DFLT_RESUME_SCHEMA_PATH
        schema = _load_json_file(schema_path)
    except FileNotFoundError:
        return []

    validator = jsonschema.Draft7Validator(schema)
    return [str(e) for e in validator.iter_errors(content)]


def validate_resume_content_dict(content: dict, *, raise_errors=True) -> ResumeDict:
    """Validate resume content using ResumeSchemaExtended (which allows extra fields)."""
    from hired.base import ResumeSchemaExtended

    try:
        _ = ResumeSchemaExtended(**content)
    except ValidationErrors as e:
        print(validation_friendly_errors_string(e))
        if raise_errors:
            raise
    return content


# --------------------------------------------------------------------------------------
# Functions that manage resources


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
    new_schema = ensure_dict(DFLT_SCHEMA_URL)
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
