"""
JSON Resume schema validation utilities.

Implement:
- Schema loading and caching
- Validation functions
- Error reporting utilities
"""

from typing import Mapping, Any
from hired.base import ResumeContent
from hired.util import _load_json_file

try:
    import jsonschema
except ImportError:
    jsonschema = None


def _load_schema() -> dict:
    """Load the JSON Resume schema from package data."""
    # For now, just return an empty schema as a placeholder
    # In real use, load from data/schemas/resume.json
    return {}


_schema_cache = None


def validate_resume_content(content: Mapping[str, Any]) -> bool:
    """Validate resume content against the JSON Resume schema."""
    global _schema_cache
    if _schema_cache is None:
        _schema_cache = _load_schema()
    if jsonschema is None:
        raise ImportError('jsonschema is required for validation')
    try:
        jsonschema.validate(instance=content, schema=_schema_cache)
        return True
    except jsonschema.ValidationError:
        return False


def _get_validation_errors(content: Mapping[str, Any]) -> list[str]:
    """Return a list of validation error messages."""
    global _schema_cache
    if _schema_cache is None:
        _schema_cache = _load_schema()
    if jsonschema is None:
        raise ImportError('jsonschema is required for validation')
    validator = jsonschema.Draft7Validator(_schema_cache)
    return [str(e) for e in validator.iter_errors(content)]
