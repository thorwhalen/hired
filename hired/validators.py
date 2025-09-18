"""
JSON Resume schema validation utilities.

Implement:
- Schema loading and caching
- Validation functions
- Error reporting utilities
"""

from typing import Mapping, Any
from hired.base import ResumeContent, ResumeBasics, ResumeWork, ResumeEducation
from hired.util import _load_json_file, _get_package_data_path
from collections.abc import Mapping as ABCMapping


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


def _load_schema() -> dict:
    """Load the JSON Resume schema from package data."""
    schema_path = _get_package_data_path('schemas/resume.json')
    try:
        return _load_json_file(schema_path)
    except FileNotFoundError:
        return {}


_schema_cache = None


def validate_resume_content(content: Mapping[str, Any], *, strict: bool = True) -> bool:
    """Validate resume content against the JSON Resume schema.

    If strict=False and schema fails, returns True (permissive mode).
    """
    global _schema_cache
    if _schema_cache is None:
        _schema_cache = _load_schema()
    if jsonschema is None:
        raise ImportError('jsonschema is required for validation')
    try:
        jsonschema.validate(instance=_prune_none(dict(content)), schema=_schema_cache)
        return True
    except jsonschema.ValidationError:
        return False if strict else True


def _get_validation_errors(content: Mapping[str, Any]) -> list[str]:
    """Return a list of validation error messages."""
    global _schema_cache
    if _schema_cache is None:
        _schema_cache = _load_schema()
    if jsonschema is None:
        raise ImportError('jsonschema is required for validation')
    validator = jsonschema.Draft7Validator(_schema_cache)
    return [str(e) for e in validator.iter_errors(content)]


def validate_with_models(raw: Mapping[str, Any]) -> ResumeContent:
    """Validate a raw resume dict using pydantic models first.

    This normalizes fields like work.company/name before schema validation.
    Raises pydantic ValidationError if structure invalid.
    """
    basics = ResumeBasics(**raw.get('basics', {}))
    work = []
    for w in raw.get('work', []) or []:
        if 'company' not in w and 'name' in w:
            w = {**w, 'company': w['name']}
        work.append(ResumeWork(**w))
    education = [ResumeEducation(**e) for e in raw.get('education', []) or []]
    # Capture extra/freeform sections (top-level keys not recognized)
    known_keys = {'basics', 'work', 'education'}
    extra_sections = {k: v for k, v in raw.items() if k not in known_keys}
    return ResumeContent(
        basics=basics, work=work, education=education, extra_sections=extra_sections
    )


def validate_and_normalize(
    raw: Mapping[str, Any], *, strict: bool = True
) -> ResumeContent:
    """Full pipeline validation: pydantic + json schema (optional strict).

    Returns normalized ResumeContent.
    Raises ValidationError if pydantic validation fails or schema invalid in strict mode.
    """
    model_content = validate_with_models(raw)
    dump = model_content.model_dump(exclude_none=True)
    dump = _prune_none(dump)
    if not validate_resume_content(dump, strict=strict):
        # gather errors only if strict
        if strict:
            errors = _get_validation_errors(dump)
            raise ValueError(f'Schema validation failed: {errors}')
    return model_content
