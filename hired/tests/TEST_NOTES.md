(## Test notes and triage guidance

This document summarizes what each test file in this folder actually exercises,
which production modules it touches, and what to do when the test fails.

Purpose: quick triage guidance — if a test fails you can read the short note
below to decide whether the test checks core functionality (high impact), or
tests a small/legacy detail that might be obsolete and safe to drop (low
impact).

Legend:
- Modules: the production modules the test touches directly
- Impact: High / Medium / Low — how broadly a failure is likely to affect
	real usage (rendering resumes, validating schema, public APIs)
- Action: short suggested triage steps

---

1) test_base.py
	 - What: Basic checks for `RenderingConfig`, `ResumeSchemaExtended`, and
		 simple `Basics` model instantiation.
	 - Modules: `hired.base`, `hired.resumejson_pydantic_models`
	 - Impact: Low — sanity checks for dataclasses/models.
	 - Action if it fails: check `resumejson_pydantic_models` definitions and
		 `base.RenderingConfig` dataclass defaults. Failures here indicate an API
		 break in the models — fix model fields or defaults.

2) test_config.py
	 - What: `ConfigStore` basic mapping behavior, `get_default_config`, and
		 `load_config` (loads a JSON file into a ConfigStore).
	 - Modules: `hired.config`, `hired.util` (indirect, because load uses util)
	 - Impact: Low-Medium — affects loading/reading configurations; not core to
		 rendering but used by optional config flows.
	 - Action if it fails: inspect `ConfigStore` methods (`__getitem__`,
		 `__setitem__`, `__delitem__`, iteration). If `load_config` fails, check
		 `_load_json_file` and file permissions/encoding.

3) test_content.py
	 - What: `DictContentSource`, `FileContentSource` (JSON), and `DefaultAIAgent`
		 stub behavior.
	 - Modules: `hired.content`, `hired.resumejson_pydantic_models`, `hired.base`
	 - Impact: Medium — these are entrypoints for reading inputs. If they break
		 people can't load resume dicts from files or dicts.
	 - Action if it fails: verify file-reading helpers (`_load_json_file`,
		 YAML loader), and that `DefaultAIAgent.generate_content` returns a
		 `ResumeSchemaExtended` instance (or equivalent dict). If you intend to
		 remove AI-agent code, only keep `DictContentSource`/`FileContentSource`.

4) test_freeform.py
	 - What: Ensures freeform/unknown sections are accepted and rendered
		 (non-strict). Also contains a skipped test that assumes strict schema
		 behavior.
	 - Modules: `hired.tools`, `hired.renderers.html` (indirect)
	 - Impact: Medium — this confirms that extra top-level keys appear in
		 `extra_sections` in HTML output. Important for custom sections.
	 - Action if it fails: check `mk_resume`'s normalization and `HTMLRenderer`'s
		 `_iter_extra_sections` / context-building. If failing but you don't use
		 extra sections, the test may be lower priority; if you allow custom
		 content, fix the HTML renderer.
	 - Note: one test is marked skipped; it references strict JSON schema
		 behavior which the current codebase handles permissively via
		 `ResumeSchemaExtended`.

5) test_integration.py
	 - What: End-to-end pipeline tests — `mk_content_for_resume` + `mk_resume`
		 producing a PDF/HTML; reading candidate/job fixtures; tests theme and
		 format handling.
	 - Modules: `hired.tools`, `hired.content`, `hired.renderers.html`,
		 `hired.render` (registry)
	 - Impact: High — covers the main user workflow (content generation ->
		 render -> output). Failures likely indicate regressions affecting
		 rendering or input handling.
	 - Action if it fails: first reproduce locally with small inputs; check
		 whether failures are due to optional dependencies (WeasyPrint /
		 RenderCV) or changes in `mk_resume` validation. Verify that
		 `mk_content_for_resume` returns a valid Pydantic model or dict.

6) test_plugin_system.py
	 - What: Tests renderer registry behavior, default renderer presence, and
		 basic RenderCV availability checks. Also performs end-to-end tests for
		 HTML and PDF rendering via the registry paths.
	 - Modules: `hired.base` (RendererRegistry), `hired.render`,
		 `hired.renderers.html`, `hired.tools`
	 - Impact: High — rendering plugin system is critical to selecting and
		 instantiating renderers. If registry logic breaks some formats may be
		 unreachable.
	 - Action if it fails: inspect `RendererRegistry.register` and
		 `get_renderer_registry()` initialization. Pay attention to caching of
		 instances (registry._instances) vs. class constructors.
	 - Note: `test_rendercv_available` is informational — it expects optional
		 deps; a failure here doesn't imply core regression unless you expect
		 RenderCV to be available.

7) test_real_example.py
	 - What: Renders a real-life sample resume and checks for name/email/HTML
		 markers. Marked skipped in current test file (skipped decorator), but
		 present and useful when enabled.
	 - Modules: `hired.tools`, `hired.util` (proj_files path helper),
		 `hired.renderers.html`
	 - Impact: Medium-High — this is a realistic smoke test that guards
		 against regressions that only show up on large/real data.
	 - Action if it fails: ensure fixtures path resolution (`proj_files`) is
		 correct and that `mk_resume` normalization handles that real JSON. If
		 test is brittle, consider slimming the assertions to a few robust
		 key-strings or enabling `strict=False` expectations.

8) test_render_templates.py
	 - What: Verifies the HTML rendering behavior: empty sections are omitted,
		 presence of basics, minimal theme rendering, and that themes include
		 expected snippets.
	 - Modules: `hired.renderers.html`, `hired.base`, `hired.resumejson_pydantic_models`
	 - Impact: High — template rendering is core. Failures indicate template
		 context or rendering logic regressions.
	 - Action if it fails: check the HTMLRenderer `_build_context` implementation
		 (filtering empty sections, core_sections set) and template files in
		 `hired/themes`. Also ensure Jinja2 environment path is correct.

9) test_render.py
	 - What: Tests `ThemeRegistry` and `HTMLRenderer` outputs for HTML and PDF
		 conversion. PDF assertions rely on WeasyPrint if present; otherwise the
		 fallback PDF builder is expected to produce a valid PDF header.
	 - Modules: `hired.renderers.html`
	 - Impact: High — PDF/HTML conversion is central to the package.
	 - Action if it fails: determine whether WeasyPrint is installed; if not,
		 inspect the minimal `_build_minimal_pdf` fallback path. Also verify that
		 `HTMLRenderer.render` properly chooses the path based on `config.format`.

10) test_util.py
		- What: Tests utility functions: `_merge_dicts` and `_load_json_file`.
		- Modules: `hired.util`
		- Impact: Medium — utilities are used across modules; failures can ripple
			but are usually straightforward to fix.
		- Action if it fails: unit-test and fix the specific util function. These
			tests are generally not obsolete.

11) test_validators.py
		- What: Tests `validate_resume_content_dict` (from `util`) accepts a
			minimal resume dict and returns normalized dict or raises appropriately.
		- Modules: `hired.util` (validation wrapper) and Pydantic models
		- Impact: High — validation changes will affect `mk_resume` and other
			flows.
		- Action if it fails: examine normalization and Pydantic conversion
			(ResumeSchemaExtended). If you plan to replace validation, update this
			test to the new validation contract. Do not delete without replacing.

---

Quick heuristics for triage when a test fails
- If `test_render*` or `test_integration.py` fails: treat as high priority —
	likely affects rendering pipeline or public API. Reproduce with minimal
	content and check the renderer path (WeasyPrint optional path can be a
	false-positive source of failure).
- If `test_content.py` or `test_config.py` fails: check file loading and
	simple mapping logic. These are medium priority unless your project uses
	these entrypoints heavily.
- If `test_validators.py` fails: validation behavior changed — high impact.
	Fix the schema normalization or update tests when intentionally altering
	validation semantics.
- If `test_freeform.py` fails and you don't use freeform sections: low
	priority — either fix or mark obsolete, but be cautious: this test checks
	behavior many users rely on to add custom sections.

Marking tests obsolete / safe to delete
- `test_*` that assert very specific strings from large real fixtures can
	be brittle. Prefer replacing brittle substring checks with smaller, robust
	assertions (e.g., that basics.name appears) before deleting.
- `test_rendercv_available` is informational — it should not block CI unless
	you intend RenderCV to be a hard dependency. Consider marking it xfail or
	skip if you don't install RenderCV dependencies in CI.

Final note
- The most important tests to keep passing are integration and renderer
	tests. Those ensure the primary function — render a JSON-resume dict to
	HTML/PDF — works. Tests that exercise deprecated / optional paths may be
	relaxed or removed after you centralize validation and confirm the public
	API surface.


