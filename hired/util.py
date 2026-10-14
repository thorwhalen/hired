"""
Utilities for external dependencies and general helpers.
All imports here are external to the hired package.
"""

from __future__ import annotations

import json
from importlib.resources import files
import os
from typing import TYPE_CHECKING, Any, Union
from collections.abc import Iterator
from collections.abc import Mapping
from pathlib import Path

import yaml  # pip install PyYAML

from hired._converters import ensure_dict
from hired.resumejson_pydantic_models import ResumeSchema

if TYPE_CHECKING:
    from importlib.abc import Traversable

    from hired.base import ResumeSchemaExtended

proj_files: Traversable = files("hired")
data_files: Traversable = files("hired") / "data"
themes_files: Traversable = data_files / "themes"


def _load_json_file(path: str) -> dict[str, Any]:
    """Load a JSON file from the given path."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


try:
    import toml

    def _load_toml_file(path: str) -> dict[str, Any]:
        with open(path, encoding="utf-8") as f:
            return toml.load(f)

except ImportError:

    def _load_toml_file(path: str) -> dict[str, Any]:
        raise ImportError("toml is required for TOML support")


def load_yaml(yaml_path: str) -> Any:
    """
    Loads a YAML file using PyYAML.
    This works in Python 3.7+ because dicts preserve insertion order.
    """
    with open(yaml_path) as file:
        # Use safe_load for security reasons.
        return yaml.safe_load(file)


def dump_yaml(d: dict[str, Any], yaml_path: str) -> None:
    """
    Dumps a dictionary to a YAML file using PyYAML,
    preserving key order and using a readable block style.
    """
    with open(yaml_path, "w") as file:
        # sort_keys=False is crucial to prevent alphabetical sorting.
        # default_flow_style=False ensures a readable, multi-line format.
        yaml.dump(d, file, sort_keys=False, default_flow_style=False)


# --------------------------------------------------------------------------------------
# Helpers
from pydantic import ValidationError as PydanticValidationError
from jsonschema.exceptions import ValidationError as JsonSchemaValidationError


def _merge_dicts(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Merge two dicts shallowly, with override taking precedence."""
    result = base.copy()
    result.update(override)
    return result


ValidationErrorType = Union[PydanticValidationError, JsonSchemaValidationError]
ValidationErrors: tuple[
    type[PydanticValidationError], type[JsonSchemaValidationError]
] = (
    PydanticValidationError,
    JsonSchemaValidationError,
)
JsonContentStr = str  # JSON string
PathStr = str  # filesystem path
ResumeSource = Union[PathStr, JsonContentStr, Path, Mapping[str, Any]]
ResumeDict = dict[str, Any]  # one that is valid in the ResumeSchema sense


def extract_friendly_errors(
    error_obj: ValidationErrorType, schema: Any = None, data: Any = None
) -> Iterator[tuple[Any, str]]:
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
            field = error["loc"][0]
            message = error["msg"]
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
    schema: Any = None,
    data: Any = None,
) -> str:
    return "\n".join(
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
            with open(content_src, encoding="utf-8") as f:
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


def _prune_none(obj: Any) -> Any:
    """Recursively remove keys or list items that are None so schema validation doesn't see explicit nulls for optional fields."""
    if isinstance(obj, dict):
        return {k: _prune_none(v) for k, v in obj.items() if v is not None}
    if isinstance(obj, list):
        return [_prune_none(x) for x in obj if x is not None]
    return obj


def normalize_and_validate_resume(
    raw: Mapping[str, Any], *, strict: bool = True
) -> ResumeSchemaExtended:
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
        raise TypeError("raw must be a mapping")

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
    content: Mapping[str, Any], schema_path: str | None = None
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


def validate_resume_content_dict(
    content: dict[str, Any], *, raise_errors: bool = True
) -> ResumeDict:
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


schemas_files: Traversable = data_files / "schemas"
resume_jsons_files: Traversable = data_files / "resume_jsons"
resume_json_example: Traversable = resume_jsons_files / "test_resume.json"

DFLT_RESUME_SCHEMA_PATH = str(schemas_files / "resume_schema.json")
DFLT_SCHEMA_URL = (
    "https://raw.githubusercontent.com/jsonresume/resume-schema/v1.0.0/schema.json"
)
DFLT_TEST_RESUME_URL = "https://raw.githubusercontent.com/jsonresume/resume-schema/refs/heads/v1.0.0/sample.resume.json"


def _rewrite_constr(code: str) -> str:
    """Rewrite ``constr(...)`` calls as ``Annotated[str, StringConstraints(...)]``.

    The same constraint, spelled so a type checker can read it as a type
    (pydantic v2; hired#35). Located with :mod:`ast`, so a regex pattern
    argument holding parentheses is never mistaken for the call's end.

    >>> _rewrite_constr('x: constr(pattern=r"^(a|b)$") = None')
    'x: Annotated[str, StringConstraints(pattern=r"^(a|b)$")] = None'
    """
    import ast

    tree = ast.parse(code)
    lines = code.splitlines(keepends=True)
    offsets = [0]
    for line in lines:
        offsets.append(offsets[-1] + len(line))

    def _char_col(lineno, byte_col):
        # ast columns count UTF-8 bytes; string slicing counts characters.
        return len(lines[lineno - 1].encode()[:byte_col].decode())

    def _span(node):
        return (
            offsets[node.lineno - 1] + _char_col(node.lineno, node.col_offset),
            offsets[node.end_lineno - 1]
            + _char_col(node.end_lineno, node.end_col_offset),
        )

    calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "constr"
    ]
    # Outermost first, then drop nested ones (constr never nests in practice).
    spans = sorted((_span(c) for c in calls), key=lambda s: (s[0], -s[1]))
    kept = []
    for start, end in spans:
        if not kept or start >= kept[-1][1]:
            kept.append((start, end))
    for start, end in reversed(kept):
        call = code[start:end]
        inner = call[call.index("(") + 1 : -1]
        code = f"{code[:start]}Annotated[str, StringConstraints({inner})]{code[end:]}"
    return code


def _fix_resume_model_typing(code: str) -> str:
    """Post-process generated model code so a type checker can read it (hired#35).

    ``constr(...)`` becomes ``Annotated[str, StringConstraints(...)]`` (imports
    adjusted), and ``model_config`` is declared ``ClassVar[ConfigDict]`` (#27),
    so a regenerated file keeps both.
    """
    import re

    if "constr(" in code:
        code = _rewrite_constr(code)
        if re.search(r"^from pydantic import \(", code, flags=re.MULTILINE):
            code = code.replace(
                "from pydantic import (", "from pydantic import StringConstraints\nfrom pydantic import (", 1
            )
        code = re.sub(
            r"^(from pydantic import )([^(\n]*)$",
            lambda m: m.group(1)
            + ", ".join(
                sorted(
                    {n.strip() for n in m.group(2).split(",") if n.strip()}
                    - {"constr"}
                    | {"StringConstraints"}
                )
            ),
            code,
            count=1,
            flags=re.MULTILINE,
        )
        code = _ensure_typing_import(code, "Annotated")
    if re.search(r"^\s+model_config = ", code, flags=re.MULTILINE):
        code = re.sub(
            r"^(\s+)model_config = ", r"\1model_config: ClassVar[ConfigDict] = ",
            code,
            flags=re.MULTILINE,
        )
        code = _ensure_typing_import(code, "ClassVar")
    return code


def _ensure_typing_import(code: str, name: str) -> str:
    """Add *name* to the module's ``from typing import ...`` line (or add one)."""
    import re

    m = re.search(r"^from typing import (.*)$", code, flags=re.MULTILINE)
    if m is None:
        future = re.search(r"^from __future__ import .*\n", code, flags=re.MULTILINE)
        at = future.end() if future else 0
        return f"{code[:at]}from typing import {name}\n{code[at:]}"
    names = {n.strip() for n in m.group(1).split(",") if n.strip()}
    if name in names:
        return code
    line = "from typing import " + ", ".join(sorted(names | {name}))
    return code[: m.start()] + line + code[m.end() :]


def refresh_resume_schema() -> None:
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
        if "AnyUrl" not in code:
            return code

        # Remove AnyUrl from imports, handling various import patterns
        # Pattern 1: from pydantic import AnyUrl, ...
        code = re.sub(
            r"from pydantic import ([^,\n]*,\s*)?AnyUrl(,\s*[^,\n]*)?",
            r"from pydantic import \1\2",
            code,
        )

        # Pattern 2: from pydantic import ..., AnyUrl
        code = re.sub(
            r"(from pydantic import [^,\n]*),\s*AnyUrl\s*$",
            r"\1",
            code,
            flags=re.MULTILINE,
        )

        # Pattern 3: from pydantic import AnyUrl only
        code = re.sub(r"from pydantic import AnyUrl\n", "", code)

        # Clean up any leftover commas from import removal
        code = re.sub(r"from pydantic import\s*,", "from pydantic import", code)
        code = re.sub(r",\s*,", ",", code)
        code = re.sub(r",\s*\)", ")", code)

        # Add the type alias definition after the imports
        lines = code.split("\n")
        import_end_idx = 0
        for i, line in enumerate(lines):
            if line.strip().startswith(
                ("from ", "import ")
            ) and not line.strip().startswith("# "):
                import_end_idx = i

        # Insert the type alias after imports
        lines.insert(import_end_idx + 1, "")
        lines.insert(import_end_idx + 2, "# Type alias to avoid strict URL validation")
        lines.insert(import_end_idx + 3, "AnyUrl = Optional[str]")
        lines.insert(import_end_idx + 4, "")

        return "\n".join(lines)

    print("Get the schema (dict) from the url")
    new_schema = ensure_dict(DFLT_SCHEMA_URL)
    print("Make pydantic models (code) from it")
    new_schema_code = pydantic_model_to_code(
        new_schema,
        egress_transform=lambda code: _fix_resume_model_typing(
            fix_anyurl_transform(code)
        ),
    )
    print("Replace the code that is in resumejson_pydantic_models.py")
    (proj_files / "resumejson_pydantic_models.py").write_text(
        f'"""Pydantic models for resume json schema\n"""\n{new_schema_code}'
    )

    print("Writing the schema in the schema file (for reference)...")
    Path(DFLT_RESUME_SCHEMA_PATH).write_text(json.dumps(new_schema))

    print("Refresh test json")
    Path(resume_json_example).write_text(json.dumps(ensure_dict(DFLT_TEST_RESUME_URL)))
