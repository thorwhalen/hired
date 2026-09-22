# hired.util

Utilities for external dependencies and general helpers.
All imports here are external to the hired package.

### Functions

| [`dump_yaml`](#hired.util.dump_yaml)(d, yaml_path)                           | Dumps a dictionary to a YAML file using PyYAML, preserving key order and using a readable block style.   |
|----------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------|
| [`ensure_resume_content_dict`](#hired.util.ensure_resume_content_dict)(content_src)           | Get a schema-valid resume dict from various sources (json file, json string, dict, ...)                  |
| [`extract_friendly_errors`](#hired.util.extract_friendly_errors)(error_obj[, schema, ...]) | Extracts a generator of user-friendly error messages from a validation error object.                     |
| [`get_jsonschema_errors`](#hired.util.get_jsonschema_errors)(content[, schema_path])     | Return a list of jsonschema validation error messages for the content.                                   |
| [`load_yaml`](#hired.util.load_yaml)(yaml_path)                              | Loads a YAML file using PyYAML.                                                                          |
| [`normalize_and_validate_resume`](#hired.util.normalize_and_validate_resume)(raw, \*[, strict])  | Normalize and validate a resume-like mapping.                                                            |
| `refresh_resume_schema`()                                                                          |                                                                                                          |
| [`validate_resume_content_dict`](#hired.util.validate_resume_content_dict)(content, \*[, ...])  | Validate resume content using ResumeSchemaExtended (which allows extra fields).                          |
| `validation_friendly_errors_string`(error_obj)                                                     |                                                                                                          |

### hired.util.dump_yaml(d, yaml_path)

Dumps a dictionary to a YAML file using PyYAML,
preserving key order and using a readable block style.

### hired.util.ensure_resume_content_dict(content_src)

Get a schema-valid resume dict from various sources
(json file, json string, dict, …)

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)

### hired.util.extract_friendly_errors(error_obj, schema=None, data=None)

Extracts a generator of user-friendly error messages from a validation error object.

This function works with both Pydantic’s ValidationError and jsonschema’s
ValidationError to provide a consistent output.

* **Parameters:**
  **error_obj** (`Union`[`ValidationError`, `ValidationError`]) – The ValidationError instance to process.
* **Yields:**
  A tuple of (field, message) for each validation error.

### hired.util.get_jsonschema_errors(content, schema_path=None)

Return a list of jsonschema validation error messages for the content.

If jsonschema is not available or the schema file is missing, returns an
empty list.

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]

### hired.util.load_yaml(yaml_path)

Loads a YAML file using PyYAML.
This works in Python 3.7+ because dicts preserve insertion order.

### hired.util.normalize_and_validate_resume(raw, , strict=True)

Normalize and validate a resume-like mapping.

- Prunes None values.
- Validates via Pydantic ResumeSchemaExtended (allows extra fields).
- If strict is True and jsonschema is available, will attempt schema
  validation against the packaged JSON schema (best-effort).

Returns a ResumeSchemaExtended instance on success. Raises
pydantic.ValidationError on failure.

### hired.util.validate_resume_content_dict(content, , raise_errors=True)

Validate resume content using ResumeSchemaExtended (which allows extra fields).

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)
