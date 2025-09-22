"""
JSON Resume schema validation utilities.

Implement:
- Schema loading and caching
- Validation functions
- Error reporting utilities
"""

from typing import Mapping, Any
from functools import lru_cache
from hired.base import ResumeContent, ResumeBasics, ResumeWork, ResumeEducation
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
