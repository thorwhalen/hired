# hired

Streamline the job application process for job seekers

## Overview

The `hired` package is a Python library designed to simplify the process of creating professional resumes tailored to specific job applications. It leverages AI-driven content generation, schema validation, and customizable rendering pipelines to produce high-quality resumes in various formats.

## Features

### 1. Content Generation
- **AI-Driven Content**: Automatically generate resume content by analyzing candidate profiles and job descriptions.
- **Flexible Sources**: Supports JSON, YAML, and Python dictionaries as input sources.

### 2. Validation
- **JSON Resume Schema**: Ensures compliance with the [JSON Resume schema](https://jsonresume.org/schema/).
- **Strict and Permissive Modes**: Validate content strictly or allow flexibility for missing fields.
- **Pruning**: Automatically removes `None` values to ensure schema compliance.

### 3. Rendering
- **HTML and PDF**: Render resumes as HTML or PDF.
- **Template-Based Themes**: Use Jinja2 templates for customizable themes (e.g., `default`, `minimal`).
- **Optional WeasyPrint Integration**: Generate professional PDFs with WeasyPrint if installed.
- **Fallback PDF Builder**: Minimal PDF generation without external dependencies.
- **Empty Section Omission**: Automatically skips rendering empty sections.

## Installation

Install the package using pip:
# hired — resume rendering toolkit

This repository contains a small toolkit for working with JSON Resume-style
data and rendering it into HTML or PDF resumes. The codebase includes a few
renderers, Pydantic models for the resume schema, simple content-source
abstractions, and a small orchestration API used by `mk_content_for_resume`
and `mk_resume`.

This README maps what's in the code, explains how to render resumes, and
gives a clear, prioritized plan for refactoring and focusing the project on
the core goal: reliably rendering resume dicts with configurable templates.

## What lives where (high-level)

- `hired/base.py` — core protocols, dataclasses, and the global renderer
    registry (Renderer, RenderingConfig, ContentSource, ResumeSchemaExtended).
- `hired/resumejson_pydantic_models.py` — Pydantic models that implement the
    JSON Resume schema (ResumeSchema and related types). These are the
    canonical data models used across the package.
- `hired/content.py` — content source implementations (`FileContentSource`,
    `DictContentSource`) and a small `DefaultAIAgent` stub that currently returns
    the candidate dict as a model. This is where you'd plug in a real LLM
    agent or content transformation pipeline.
- `hired/tools.py` — the public, user-facing functions: `mk_content_for_resume`
    and `mk_resume`. These coordinate reading inputs, generating/validating
    content, selecting a renderer, and writing output.
- `hired/render.py` — renderer registry + helper to pick the renderer for a
    format (html/pdf/rendercv). It registers the built-in renderers.
- `hired/renderers/html.py` — Jinja2-based HTML renderer and a small Theme
    registry; converts the pydantic model to a sanitized template context. It
    contains HTML -> PDF conversion using WeasyPrint when available, otherwise a
    minimal fallback PDF builder.
- `hired/renderers/rendercv.py` — RenderCV integration that converts JSON
    Resume to RenderCV format and produces higher-quality PDFs (requires
    optional dependencies). The implementation includes robust fallbacks and
    warnings to help when data is incomplete.
- `hired/config.py` — a tiny ConfigStore wrapper used for storing rendering
    defaults and loading external config files.
- `hired/util.py` — helpers for loading JSON/YAML, merging dicts, and
    validation helpers used by multiple modules.
- `hired/validators.py` — a backwards-compatible layer around schema
    validation; marked deprecated inside the codebase. Prefer `util.validate_*`
    helpers and the Pydantic models.
- `hired/themes/` — Jinja2 templates used by the HTML renderer (`default.html`,
    `minimal.html`).
- `tests/` and `tests/fixtures/` — unit tests and sample resume fixtures.

Files/areas that are duplicated or safe to consider removing:
- `hired/validators.py` mostly delegates to the utilities in `util.py` and is
    documented as deprecated in the code. Keep only for compatibility or remove.
- Any helper duplication between `util.py` and small functions in
    `renderers/rendercv.py` should be consolidated into `util.py` or moved to a
    single `converters/` submodule.

## Quick start — render a resume dict

The simplest usage from the current API:

1) Produce or load a resume dictionary (already in JSON Resume shape).

2) Render it:

```python
from hired.tools import mk_resume
from hired.base import RenderingConfig

# `resume_dict` should match the JSON Resume structure (or ResumeSchemaExtended)
result_bytes = mk_resume(resume_dict, RenderingConfig(format='pdf', theme='default'))
# if you want HTML instead: RenderingConfig(format='html', theme='minimal')

# mk_resume will return bytes; it also accepts output_path= to write file.
```

How to try different templates:
- Change the `theme` argument in `RenderingConfig` (themes live in
    `hired/themes/`).
- If you need a custom template file, either:
    - Edit or add files under `hired/themes/` and pick the new `theme` name, or
    - Create a small ThemeRegistry and pass it to the `HTMLRenderer` constructor
        (advanced).

Inserting custom changes / custom sections:
- Pass extra keys at the top level of the resume dict — the HTML renderer
    collects keys not in the core schema and exposes them as `extra_sections`
    (rendered as small HTML fragments). That is the supported extension path
    for custom content.

## What to improve / refactor (recommended, ordered)

1) Make a small, clear public API surface
     - Keep `hired.tools.mk_content_for_resume` and `mk_resume` as the public
         entry points. They are already the convenience functions tests use.
     - Move internal helpers to `hired._impl.*` or clearly private functions.

2) Consolidate validation
     - Delete or archive `hired/validators.py` (it's flagged deprecated). Use a
         single `util.validate_resume_dict()` that returns a normalized
         `ResumeSchemaExtended` Pydantic model or raises a ValidationError.
     - Make `mk_resume` always convert dict -> `ResumeSchemaExtended` via a
         single helper (normalize + validate + prune None).

3) Refactor renderers into a small plugin system
     - Keep `hired/renderers/` as the extension point. Make each renderer a
         small class exposing `render(content, config) -> bytes` (already in
         place).
     - Simplify `hired/render.py` to only manage registration and discovery.

4) Templates & themes
     - Move theme discovery into a ThemeManager with a simple API to load a
         custom template path or a packaged theme. Make `RenderingConfig` accept
         `custom_template` and have `HTMLRenderer` prefer that when present.

5) Remove or simplify AI agent pieces
     - `DefaultAIAgent` is a stub; either implement the intended LLM logic or
         delete it and focus on deterministic content transforms. Keep agent
         interfaces if you plan to plug an LLM later.

6) Tests & CI
     - Clean test fixtures to one canonical real example. Add one or two
         focused tests for: HTML rendering, PDF rendering (WeasyPrint optional),
         and conversion to RenderCV if that backend is intended to be supported.

Suggested low-risk initial changes to implement now:
- Centralize schema validation into a single function in `util.py`.
- Have `mk_resume` accept `RenderingConfig(custom_template=...)` and wire it
    into `HTMLRenderer` (small edit to `renderers/html.py`).
- Add a small CLI wrapper `bin/hired-render` (argparse) that calls `mk_resume`.

## Notes on RenderCV and PDF quality

- `hired/renderers/rendercv.py` provides a higher-quality PDF pipeline via
    `jsonresume-to-rendercv` and `rendercv` but requires optional
    dependencies. Keep this renderer as an optional plugin and document its
    install extras (e.g. `pip install hired[rendercv]`). When enabled it will
    be registered as `rendercv` / `pdf-rendercv` and can be selected in
    `RenderingConfig.format`.

## Obsolete / deprecated pieces

- `hired/validators.py`: marked deprecated in-code — delegate to `util.py`.
- Small duplication between `config.py` / `base.py` / `render.py` for
    renderer registration — consolidate registry code in `base.py` or
    `render.py` but avoid duplicated init logic.

## Next steps I can take for you

- I can make the small, low-risk changes now (suggested above): centralize
    validation, wire `custom_template` through `RenderingConfig` ->
    `HTMLRenderer`, and update the README to include CLI + examples.
- Or I can produce a PR that removes `hired/validators.py` and ensures all
    tests still pass.

If you want, tell me which of the above I should implement next; I can
start with the `custom_template` wiring and a README update for examples and
then run the test suite to ensure no regressions.

