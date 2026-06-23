# Design: Candidate Knowledge Base + JD Alignment subsystem

Status: **active** · Owner: repo maintainer · Research basis: `misc/docs/research/`

This document is the single source of truth (SSOT) for the candidate-knowledge and
JD-alignment subsystem. The GitHub **epic** issue links here; sub-issues implement
slices of it. It encodes the architecture, schemas, storage layout, and the
decisions taken (see "Decisions" at the end).

---

## 1. Purpose

Given one or more **job descriptions (JDs)** and an accumulating body of knowledge
about a **candidate**, produce an *honest, non-exaggerating* alignment analysis that
sorts each JD requirement into four buckets:

1. **strong match** — candidate clearly has it.
2. **adjacent / transferable** — not exact, but close enough that the candidate's
   experience is a real asset.
3. **gap, learnable** — missing, but learnable enough to (a) speak intelligently in an
   interview after light study and (b) ramp up on the job — *especially* given the
   candidate's standing leverage of AI agents when working.
4. **gap, hard-to-learn** — missing and genuinely hard to acquire (tacit judgment,
   enduring aptitude, expert intuition).

The analysis must **never exaggerate** (no false positives) and — equally important —
**never assume absence from silence** (no false negatives). Anything the system does
not *know* becomes a **clarifying question to the candidate**, not a confirmed gap.

Every interaction (questions asked, answers given) is **persisted and distilled** into
reusable knowledge about the candidate, so the system gets sharper across JDs over time.

## 2. Three-layer architecture (separation of intelligence)

| Layer | What it is | Where it lives |
|---|---|---|
| **Primitives (the hands)** | Persistence, schemas, deterministic scoring/aggregation, report rendering, question-ranking math. No mandatory LLM. | `hired/` package (Python) |
| **Orchestration (the loop)** | Skills + subagents that drive ingest → elicitation → alignment → report, using **Claude as the brain** for interactive use. | `.claude/skills/`, `.claude/agents/` (committed) |
| **Optional injected LLM (autonomous)** | Library-mode analyzer driven by an injected client (openai), behind the `ai` extra, lazy — like `LLMResumeAgent`. | `hired/` (deferred; Phase 2) |

This honors the **import-safety contract**: `import hired` and the core surface work
with only the core deps + `dol`, no secrets, no LLM. The "intelligence" is supplied
either by the Claude Code agent (interactive) or an injected client (autonomous).

## 3. Module layout

```
hired/
  persistence/          # dol-based storage foundation (Storage v2)
    __init__.py
    base.py             # app_data_dir(), codec store factories, UserStore + JDStore
    repository.py       # Repository base over MutableMapping
    migrate.py          # one-time legacy-flat -> v2 migration (+ auto ensure_v2)
  candidate/            # candidate knowledge domain
    __init__.py         # facades: CandidateKnowledgeBase, JDWorkspace
    base.py             # Fact, Provenance, QAEntry, enums (pydantic v2); slug()
    knowledge_base.py   # user-level: facts / qa / raw sources / synopsis; kb.jd(), kb.jds()
    workspace.py        # JDWorkspace: per-engagement reports / company / prep / jobs
    ingest.py           # raw upload -> atomic facts (agent-assisted; deterministic glue)
  alignment/            # JD alignment domain
    __init__.py         # facade: JDAlignmentAnalyzer
    base.py             # Requirement, RequirementRecord, Evidence, AlignmentReport, enums
    rubric.py           # deterministic two-axis bucket assignment + ai-leverage modifier
    elicitation.py      # question ranking (info-gain x criticality), routing, stop criteria
    report.py           # AlignmentReport -> markdown
```

Existing modules **composed, not duplicated**: `matching.JobMatcher` (keyword layer)
becomes one input signal to `alignment`; `job_utils.JobAnalyzer` parses JDs;
`search.JobResult` is the JD carrier; `tracking` records applications.

## 4. Storage (dol, codecs, two-level layout)

**Canonical root:** `~/.local/share/hired/` (XDG `$XDG_DATA_HOME/hired`), overridable
via `HIRED_DATA_DIR`. All persistence is **outside the repo**. Resolved by
`hired.persistence.app_data_dir()`.

**Two-level per-candidate layout.** Each candidate's data is split into *what is true
about the candidate* (cross-JD, reusable) and *work on one company's role(s)*:

```
~/.local/share/hired/
  users/
    me/                          # default candidate; resolves "I"/"me"/"default"
      user/                      # the candidate — single source of truth (cross-JD)
        raw/                     # raw sources the user provided (bytes; real filenames)
        info/                    # agent-maintained, operable knowledge (agent CRUDs here)
          facts/  <id>.json      # atomic facts
          qa/     <id>.json      # Q&A history
          topics/ <topic>/...    # per-subject dossiers (overview.md + detail; Phase 2)
          synopsis.md            # regenerated overview = entry point (singleton)
          state.json             # refresh bookkeeping (Phase 3)
      jds/<jd_id>/               # one engagement = 1+ related JDs of the same company
        meta.json                # company, label, created
        jobs/ <id>.json          # JDs + parsed requirements
        reports/ <id>.json       # current alignment report per role
        report_history/ <id>/<stamp>.json   # archived prior report versions
        company/ <slug>.json     # company / people research
        interview_prep/ <slug>.json         # interview-prep briefings
  applications/                  # migrated from ~/.hired/applications.db (Decision 2)
  resume_agent_sessions/         # migrated from ~/.cache/hired/ (Decision 2)
```

**Codecs (the extension fix).** Store keys are domain-oriented and *extension-less*
on the `MutableMapping` facade; extensions live only on the filesystem side, applied
by `dol` **key codecs**, and values are dicts in Python / JSON on disk via **value
codecs**: `json_store` (`dol.Jsons`: bare-id keys, `<id>.json`, dict values),
`markdown_store` (bare keys, `<key>.md`, `str`), `bytes_store` (raw filenames kept —
there the extension *is* the meaningful key, e.g. `cv.pdf`). Singletons
(`synopsis.md`, `state.json`, `meta.json`) are single files whose accessors carry the
extension in the path, never in a store key. (dol file stores are recursive, so each
store is rooted at a directory holding only its own homogeneous files.)

**Facades.** `UserStore` groups the user-level stores; `JDStore` groups one
engagement's stores. `CandidateKnowledgeBase` is the user-level domain facade
(`add_fact`, `facts`, `record_qa`, `save_upload`, `synopsis`); `JDWorkspace` (reached
via `kb.jd(jd_id, company=…, label=…)`) is the per-engagement facade (`save_report`,
`get_report`, `report_versions`, `save_company_report`, `save_briefing`, `save_job`).
Repositories wrap the json stores with pydantic validation. Multi-tenant is reachable
by adding `users/<other>/`; the default-user resolution is the only single-tenant
assumption, and it is isolated.

**Migration.** `hired.persistence.migrate` moves a legacy *flat* `users/<user>/<kind>/`
layout (extension-less files) to this v2 layout once, idempotently — grouping a
company's several role reports + its shared research + prep into one engagement by
default. It runs automatically on first v2 access (`ensure_v2`) or explicitly
(`migrate_user_to_v2`, with a `dry_run` plan).

## 5. Knowledge schemas (open-world, provenance-first)

**Enums:** `ConfidenceLevel{HIGH,MEDIUM,LOW}`, `MatchState{CONFIRMED,CONTRADICTED,UNKNOWN}`,
`FactStatus{ASSERTED,SUPERSEDED}`.

**`Provenance`**: `source_kind{upload,qa,inferred,external}`, `source_id`, `locator`
(e.g. `experience[2]`, `qa/abc123`), `quote` (verbatim; MUST be a substring of the
source when source is text — anti-hallucination invariant), `captured_at`.

**`Fact`** (atomic, one claim per record): `id`, `subject` (default `"me"`),
`category` (`skill|experience|education|achievement|preference|credential|trait|other`),
`statement` (atomic NL claim), `value` (optional structured payload), `confidence`,
`provenance: list[Provenance]`, `status`, `supersedes: id|None`, `tags`, timestamps.
**Open-world rule:** the *absence* of a fact is never a negative claim; only an explicit
`CONTRADICTED`-bearing fact (e.g. candidate said "I have not done X") asserts absence.

**`QAEntry`**: `id`, `question`, `answer`, `asked_for_job` (optional), `fills_field`,
`derived_fact_ids`, `created_at`. Q&A is append-only history; facts are the distilled,
updatable projection.

**Synopsis** is a *regenerated projection* of the fact store (never hand-edited), kept
human-readable for fast agent context-loading.

## 6. Alignment schemas

**Enums:** `Bucket{STRONG_MATCH,ADJACENT_TRANSFERABLE,GAP_LEARNABLE,GAP_HARD}`,
`MatchType{DIRECT,ADJACENT,NONE}`, `RequirementClass{GATE_KEEPER,DIFFERENTIATOR,VALUE_ADD}`,
`SkillType{TECHNICAL,DOMAIN_KNOWLEDGE,SOFT_SKILL,CREDENTIAL}`,
`Closeability{QUICK_WIN,LEARNABLE,REQUIRES_EXPERIENCE,STRUCTURALLY_HARD}`,
`AILeverage{HIGH,MEDIUM,LOW,NONE}`.

**`Requirement`**: `id`, `text` (verbatim from JD), `skill_type`, `requirement_class`,
`required_level` (0–5).

**`RequirementRecord`** (the heart):
- match: `match_state` (3-valued), `field_completeness{open,closed}`, `bucket|None`,
  `match_type`, `required_level`, `candidate_level`, `gap_size`.
- adjacency: `source_skill`, `adjacency_basis`, `transferability{direct,contextual,foundational,limited}`.
- closeability: `closeability`, `close_method{course,certification,practice_project,on_the_job,credential}`,
  `time_to_close{days,weeks,months,years}`, **`ai_leverage`** (how much the candidate's
  standing AI-agent capability lowers the effective ramp — a first-class modifier).
- evidence/confidence: `confidence`, `uncertainty_reason`, `evidence: Evidence|None`.
- loop: `impact` (1–5), `info_gain` (float), `needs_clarification`, `talking_point`.

**`Evidence`**: `quote` (verbatim), `source_document_id`, `locator`.

**`AlignmentReport`**: `verdict{recommendation: apply|stretch|do_not_apply, confidence,
headline, key_reasons[≤5], has_blocking_gaps}`, `meta`, `score_summary{fit_band,
bucket_counts, ats_readability?}`, `requirements[]`, `blocking_gaps[]`,
`next_actions[≤3]`, `interview_prep{story_library, talking_points, proactive_disclosure}`,
`clarifications[]`.

**0–5 level scale:** 0 None · 1 Aware · 2 Beginner · 3 Competent · 4 Proficient · 5 Expert.

## 7. The classification rubric (two axes + AI-leverage)

For each requirement R vs candidate background B:

- **Axis A — transfer distance:** direct match / adjacent / far. Sources: exact &
  taxonomy (ESCO) skill match, keyword overlap (`matching.JobMatcher`), and — Phase 2 —
  embedding/graph adjacency. Phase 1: Claude judges A grounded in KB facts + evidence quotes.
- **Axis B — trainability:** is the gap Knowledge/explicit/near-transfer (learnable) or
  Ability/tacit/far-transfer/expert-intuition (hard)?
- **AI-leverage modifier:** when the gap is *breadth-of-knowledge* or *codified skill*
  (not tacit judgment/aptitude), a candidate who works with armies of AI agents ramps
  far faster → shift `closeability` toward `LEARNABLE`/`QUICK_WIN`. This does **not**
  rescue gaps that are genuinely tacit/aptitude-bound (those stay `GAP_HARD`).

Bucket assignment (only when `match_state ≠ UNKNOWN`):

| Bucket | Condition |
|---|---|
| `STRONG_MATCH` | `match_type=direct` AND `candidate_level ≥ required_level`, evidence present |
| `ADJACENT_TRANSFERABLE` | `match_type=adjacent` — related skill partially covers it |
| `GAP_LEARNABLE` | residual gap AND `closeability ∈ {quick_win, learnable}` (post AI-leverage) |
| `GAP_HARD` | residual gap AND `closeability ∈ {requires_experience, structurally_hard}` |
| *(no bucket — route to clarification)* | `match_state=UNKNOWN` on an **open**, decision-relevant, high-info-gain field |

## 8. The honesty / elicitation loop

1. Decompose JD → `Requirement[]` (verbatim, classified by importance).
2. For each requirement, gather evidence from the KB (facts + quotes). Set `match_state`:
   `CONFIRMED` (evidence), `CONTRADICTED` (explicit negative or missing-on-closed-field),
   else `UNKNOWN`.
3. Classify the non-UNKNOWN into buckets via the rubric.
4. Rank `UNKNOWN`, decision-relevant requirements by **info-gain ≈ profile-uncertainty ×
   requirement-criticality**; generate the most informative clarifying questions first.
5. Ask the candidate. Record each Q&A. Extract atomic facts (with provenance) and update
   the KB. Re-classify affected requirements (non-monotonic — verdicts may change).
6. **Stop** when decision-stable (no remaining unknown could flip the verdict), or a
   confidence/coverage threshold is met, or the top question's info-gain < ε, or a budget
   cap is hit.
7. Render the `AlignmentReport` (verdict-first, evidence-quoted, banded — never a single
   false-precision %), plus recruiter talking points and interview prep.

## 9. Skills & subagents (committed to repo)

- **Skill `hired-align`** — orchestrates the full workflow for the interactive (Claude-as-brain)
  path: load candidate synopsis → ingest any new uploads → analyze a JD → run the
  elicitation loop with the user → persist Q&A + facts → render the report. Knows the
  storage layout and the package API.
- **Subagent `hired-profile-ingest`** — reads raw upload files (PDF/MD/JSON/HTML), extracts
  atomic facts with provenance + confidence, returns them for persistence. Read-only on
  the repo; writes only to the external data dir via the package.
- **Subagent `hired-requirement-analyst`** (optional, parallelizable) — given one requirement
  + relevant KB facts, returns a classified `RequirementRecord` with evidence + uncertainty.

## 10. Decisions

1. **`dol` → core dependency.** Pure-Python, lightweight; becomes the SSOT for persistence.
   `tests/test_import_safety.py` updated to permit it. (User decision.)
2. **Unify storage roots now.** Migrate `tracking.py` (`~/.hired/`) and `resume_agent`
   `SessionStore` (`~/.cache/hired/`) onto `~/.local/share/hired/` with back-compat
   (read legacy path if present; one-time migrate). (User decision.)
3. **Phase 1 = just enough for the 3-JD workflow.** Persistence + schemas + repositories +
   profile ingest + the elicitation/alignment skill & subagents (Claude as brain). Heavy ML
   (ESCO adjacency graph, embeddings, conformal abstention, library-mode openai analyzer,
   multi-tenant surface) deferred to Phase-2 sub-issues. (User decision.)

## 11. Privacy

No candidate data or JD content is ever committed. Uploads, facts, Q&A, jobs, and reports
live only under `~/.local/share/hired/`. Tests use a temp `HIRED_DATA_DIR` and synthetic
fixtures — never real profile data.
