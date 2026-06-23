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
- **Candidate knowledge + JD alignment** (epic #4) — `persistence/` (dol-based
  storage: `app_data_dir`, codec store factories, `UserStore`/`JDStore`, `Repository`,
  `migrate`), `candidate/` (open-world `Fact`/`QAEntry` schemas + `CandidateKnowledgeBase`
  (user-level) + `JDWorkspace` (per-engagement) + document ingest + `state` (per-source
  digests) + `topics` (subject dossiers) + `refresh` (soft/hard, `ingest_fn`-driven);
  cross-session knowledge via `add_source`, `record_qa(derived_facts=…)`, `add_note`,
  `refresh`/`needs_refresh`), `alignment/`
  (`Requirement`/`RequirementRecord`/
  `AlignmentReport` + the deterministic two-axis rubric with the AI-leverage
  modifier + elicitation ranking + markdown report). **Intelligence is external**
  (the `hired-align` skill / injected LLM); the package is storage + schemas +
  deterministic scoring. Full spec: `misc/docs/DESIGN.md`; research in
  `misc/docs/research/`.

The public API is `hired/__init__.py` (eager core + `__all__`; the agent surface,
candidate KB, and alignment surface are lazy via `__getattr__`).

## Persistence (all outside the repo) — Storage v2

One canonical data root, `~/.local/share/hired/` (XDG; `$HIRED_DATA_DIR` override),
resolved by `hired.persistence.app_data_dir()`. Per-candidate data under
`users/<user>/` (default `me`) is split two levels:

- `user/` — the candidate (cross-JD, reusable): `raw/` (raw sources, bytes) +
  `info/` (agent-maintained: `facts/`, `qa/`, `synopsis.md`, `topics/`, `state.json`).
- `jds/<jd_id>/` — one engagement (1+ related roles of one company): `meta.json`,
  `jobs/`, `reports/`, `report_history/`, `company/`, `interview_prep/`.

**Codecs:** keys are extension-less on the facade; the filesystem side carries
extensions via dol key codecs and dicts↔JSON via value codecs — `json_store`
(`Jsons`, `<id>.json`), `markdown_store` (`<key>.md`), `bytes_store` (real filenames).
Singletons (`synopsis.md`/`state.json`/`meta.json`) are single files. Facades:
`UserStore`/`CandidateKnowledgeBase` (user-level) and `JDStore`/`JDWorkspace`
(per-engagement, via `kb.jd(jd_id, company=…, label=…)`). `persistence.migrate`
moves the legacy flat layout → v2 once (auto via `ensure_v2`, or `migrate_user_to_v2`).
`tracking` and `resume_agent` sessions live at the root (migrated from legacy
`~/.hired/` and `~/.cache/hired/` on first use). **No candidate data or JDs are ever
committed** — tests use a temp `HIRED_DATA_DIR`.

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

## Agent tooling (skills & subagents)

Real skill files live in top-level `skills/<name>/`; `.claude/skills/<name>` are
relative symlinks into them (so Claude Code finds them and `gh skill` can discover/
install them). Subagents stay in `.claude/agents/`.

- **Skill `hired-usage`** — end-user resume/search/match/ATS/cover-letter/tracking.
- **Skill `hired-dev`** — developing the package (import-safety, extension points).
- **Skill `hired-align`** (`skills/hired-align/`) — orchestrates the
  candidate-knowledge + JD-alignment workflow (ingest → classify → ask → refresh →
  report). The operational guide for the epic-#4 subsystem.
- **Skill `hired-interview-prep`** (`skills/hired-interview-prep/`) — prep for
  a headhunter call / interview: refresh report → research company → gap-focused study
  briefings that anchor JD terminology to the candidate's own experience.
- **Subagent `hired-profile-ingest`** — raw documents → atomic, provenance-bearing facts.
- **Subagent `hired-requirement-analyst`** — classify JD requirements vs facts (parallelizable).
- **Subagent `hired-alignment-report`** — canonical generator: all evidence → a full
  report, unanchored by any existing report (reusable standalone; heavy-review's fresh opinion).
- **Subagent `hired-alignment-review`** — light (patch false negatives from new Q&A) /
  heavy (regenerate + adversarial diff via `alignment.diff_reports`) report refresh;
  proposes changes for approval, never auto-applies.
- **Subagent `hired-company-research`** — company + people research for interview prep.
- **Subagent `hired-interview-prep`** — study briefings tying terminology to the
  candidate's own concepts by analogy.

Handoffs live in `.claude/handoffs/` (gitignored).
