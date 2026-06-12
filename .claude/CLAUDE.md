# hired — developer context

`hired` is an AI-assisted **job-application suite**: tailor a resume to a job,
render it (HTML/PDF/Markdown via the JSON Resume schema), search jobs across
boards, and support the application (matching, ATS check, cover letter,
tracking).

## Architecture

- **Core resume pipeline:** `tools.py` (`mk_content_for_resume` → `mk_resume`) →
  `content.py` (content sources + AI agents) → `render.py` → `renderers/`
  (`html.py`, `rendercv.py`). `base.py` holds the `ContentSource`/`AIAgent`/
  `Renderer` protocols, `ResumeSchemaExtended`, and the renderer registry.
- **`search/`** — plugin subpackage: `JobSearchSource` ABC + `SourceRegistry` +
  `JobSources` facade; sources in `search/sources/` (jobspy/adzuna/usajobs).
- **Workflow helpers** (flat in `hired/`): `matching.py`, `ats_checker.py`,
  `cover_letter.py`, `tracking.py`, `job_utils.py`.
- **`resume_agent.py`** — the large conversational AI agent (`ResumeSession`,
  `ResumeExpertAgent`, `LLMConfig`), exposed lazily from `__init__`.

The public API is `hired/__init__.py` (eager core + `__all__`; the agent surface
is lazy via `__getattr__`).

## The import-safety contract (key invariant)

`import hired` and the core surface MUST work with only the **5 core deps**
(`pydantic`, `jinja2`, `jsonschema`, `PyYAML`, `requests`) and **no secrets**.

- Every heavy/optional integration is an **extra** and imported **lazily/guarded**:
  `pdf`(weasyprint), `rendercv`(rendercv + jsonresume-to-rendercv), `search`(jobspy),
  `ai`(openai), `supervisor`(langchain). Never import them at module top level.
- `LLMResumeAgent` imports `openai` only on use (or inject a `client`);
  `DefaultAIAgent` is a pass-through mock (the default).
- The conversational agent (`resume_agent.py`) is exposed lazily.
- No module reads a secret at import time (the search sources `.get()` env vars
  defensively — keep it that way).

`tests/test_import_safety.py` pins this — keep it green.

## Dependencies / extras

| Tier | Packages |
|---|---|
| core | pydantic, jinja2, jsonschema, PyYAML, requests |
| `pdf` | weasyprint (system libs: cairo/pango) |
| `rendercv` | rendercv, jsonresume-to-rendercv |
| `search` | python-jobspy |
| `ai` | openai |
| `supervisor` | langchain, langchain-core, langchain-openai |

## Tests / CI

```bash
python -m pytest hired/ tests/ --doctest-modules -q   # core-dep run
```

- Mock the LLM (inject a fake `client`); never hit the network or need secrets.
- Heavy paths are skipped (weasyprint/jobspy) when the extra is absent.
- Several modules carry *illustrative* (non-runnable) docstring snippets and are
  excluded from `--doctest-modules` via `[tool.wads.ci.testing].exclude_paths`
  (follow-up: convert to real doctests).

## Known / deferred

- `DefaultAIAgent` is a mock; `LLMResumeAgent` is the real (opt-in, injected) AI.
- `search/__init__.py` instantiates default source singletons at import (benign —
  env reads are defensive). Deferring instantiation is a noted future cleanup.

Handoffs live in `.claude/handoffs/` (gitignored).
