"""
Resume validation utilities.

DEPRECATED: This module is deprecated. Use util.validate_resume_dict() instead,
which provides the same functionality with the new ResumeSchemaExtended approach.

The functions in this module are maintained for backward compatibility but
delegate to the new validation system.
"""

from typing import Mapping, Any
from functools import lru_cache
from hired.base import ResumeSchemaExtended
from hired.resumejson_pydantic_models import Basics, WorkItem, EducationItem
from hired.util import _load_json_file, DFLT_RESUME_SCHEMA_PATH


def _prune_none(obj):
    """Recursively remove keys or list items that are None so schema validation doesn't see explicit nulls for optional fields."""
    if isinstance(obj, dict):
        return {k: _prune_none(v) for k, v in obj.items() if v is not None}
    if isinstance(obj, list):
        return [_prune_none(x) for x in obj if x is not None]
    return obj


try:
    import jsonschema
except ImportError:
    jsonschema = None


@lru_cache
def resume_schema(schema_path: str = DFLT_RESUME_SCHEMA_PATH) -> dict:
    """Load the JSON Resume schema from package data."""
    try:
        return _load_json_file(schema_path)
    except FileNotFoundError:
        return {}


def validate_resume_content(
    content: Mapping[str, Any],
    *,
    strict: bool = True,
    schema_path: str = DFLT_RESUME_SCHEMA_PATH,
) -> bool:
    """Validate resume content against the JSON Resume schema.

    If strict=False and schema fails, returns True (permissive mode).
    """
    _resume_schema = resume_schema(schema_path)
    if jsonschema is None:
        raise ImportError('jsonschema is required for validation')
    try:
        jsonschema.validate(instance=_prune_none(dict(content)), schema=_resume_schema)
        return True
    except jsonschema.ValidationError:
        return False if strict else True


def _get_validation_errors(
    content: Mapping[str, Any], schema_path: str = DFLT_RESUME_SCHEMA_PATH
) -> list[str]:
    """Return a list of validation error messages."""
    _resume_schema = resume_schema(schema_path)
    if jsonschema is None:
        raise ImportError('jsonschema is required for validation')
    validator = jsonschema.Draft7Validator(_resume_schema)
    return [str(e) for e in validator.iter_errors(content)]


def validate_with_schema(
    raw: Mapping[str, Any], schema_path: str = DFLT_RESUME_SCHEMA_PATH
) -> ResumeSchemaExtended:
    """Validates using JSON schema first, then pydantic models.

    This function is deprecated. Use util.validate_resume_dict instead.
    """
    # For now, just delegate to the simplified approach
    return ResumeSchemaExtended(**raw)


def validate_and_normalize(
    raw: Mapping[str, Any], *, strict: bool = True
) -> ResumeSchemaExtended:
    """Full pipeline validation: pydantic + json schema (optional strict).

    Returns normalized ResumeSchemaExtended.
    Raises ValidationError if pydantic validation fails or schema invalid in strict mode.

    This function is deprecated. Use util.validate_resume_dict instead.
    """
    return ResumeSchemaExtended(**raw)
