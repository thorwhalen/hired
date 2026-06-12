---
name: hired-dev
description: Use when developing or modifying the `hired` package itself — adding a renderer or job-search source, working on the resume pipeline / AI agents (`tools.py`, `content.py`, `resume_agent.py`), the workflow helpers, or hired's dependencies/CI. Triggers on editing files under the hired repo, "add a job source to hired", "add a renderer", "wire the AI agent", or changing hired's extras.
---

# Developing `hired`

A job-application suite. See `.claude/CLAUDE.md` for the architecture map and the
dependency/extras table.

## The rule that constrains everything: import-safety

`import hired` and the core surface MUST work with only the 5 core deps
(pydantic, jinja2, jsonschema, PyYAML, requests) and **no secrets**.

- Keep heavy integrations (weasyprint, openai, rendercv, jobspy, langchain) in
  **extras**, imported **lazily / try-except-guarded**, never at module top level.
- Expose the big `resume_agent` surface lazily via `__getattr__` in `__init__`.
- No secret reads at import time.
- `tests/test_import_safety.py` pins this — run it after any import change.

When adding an optional dependency: add an extra, import it lazily (or guard with
try/except), and if its module can't import without it, list the module in
`[tool.wads.ci.testing].exclude_paths` and `importorskip` its tests.

## Extension points

- **Renderer:** implement the `Renderer` protocol and register via the renderer
  registry / `@register_renderer` (see `base.py`, `render.py`, `renderers/`).
- **Job source:** subclass `JobSearchSource` (`search/base.py`) and register with
  `SourceRegistry` (`search/registry.py`); the `JobSources` facade picks it up.
- **AI agent:** implement `generate_content(candidate, job) -> ResumeSchemaExtended`
  (the `AIAgent` protocol). `mk_content_for_resume(..., agent=...)` is the DI seam;
  `LLMResumeAgent` is the reference real implementation (lazy openai, injectable
  `client` for tests).

## Tests / CI conventions

```bash
python -m pytest hired/ tests/ --doctest-modules -q
```

Mock the LLM (inject a fake `client`), never hit the network or require secrets.
Some modules' docstrings are illustrative snippets (not runnable doctests) and
are excluded from `--doctest-modules` — converting them to real doctests is a
worthwhile follow-up. Owner style: keyword-only args beyond the first positional,
module docstrings (ruff `D100`), dataclasses for data.
