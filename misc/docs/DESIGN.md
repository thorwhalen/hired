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
  persistence/          # NEW — dol-based storage foundation (Phase 1)
    __init__.py
    base.py             # app_data_dir(), store factories, CandidateMall (store-of-stores)
    repository.py       # Repository base over MutableMapping
  candidate/            # NEW — candidate knowledge domain (Phase 1)
    __init__.py         # facade: CandidateKnowledgeBase
    base.py             # Fact, Provenance, QAEntry, enums (pydantic v2)
    knowledge_base.py   # repository over the mall: facts / qa / uploads / synopsis
    ingest.py           # raw upload -> atomic facts (agent-assisted; deterministic glue)
  alignment/            # NEW — JD alignment domain (Phase 1)
    __init__.py         # facade: JDAlignmentAnalyzer
    base.py             # Requirement, RequirementRecord, Evidence, AlignmentReport, enums
    rubric.py           # deterministic two-axis bucket assignment + ai-leverage modifier
    elicitation.py      # question ranking (info-gain x criticality), routing, stop criteria
    report.py           # AlignmentReport -> markdown
```

Existing modules **composed, not duplicated**: `matching.JobMatcher` (keyword layer)
becomes one input signal to `alignment`; `job_utils.JobAnalyzer` parses JDs;
`search.JobResult` is the JD carrier; `tracking` records applications.

## 4. Storage (dol, repository pattern)

**Canonical root:** `~/.local/share/hired/` (XDG `$XDG_DATA_HOME/hired`), overridable
via `HIRED_DATA_DIR`. All persistence is **outside the repo**. Resolved by
`hired.persistence.app_data_dir()`.

**Layout (store-of-stores / "mall"):**

```
~/.local/share/hired/
  users/
    me/                       # default candidate; resolves "I"/"me"/"default"
      uploads/                # raw bytes: CVs, bios, publications (key = filename)
      facts/                  # one JSON per atomic fact (key = fact id)
      qa/                     # one JSON per Q&A entry (key = qa id)
      jobs/                   # JDs + parsed requirements (key = job id)
      reports/                # alignment reports (key = job id)
      synopsis/               # regenerated human-readable projections (key = topic)
  applications/               # migrated from ~/.hired/applications.db (Decision 2)
  resume_agent_sessions/      # migrated from ~/.cache/hired/ (Decision 2)
```

Each leaf is a `MutableMapping` (dol file store + JSON codec). A `CandidateMall`
groups them and resolves the default user. Repositories wrap the mall with
domain methods (`add_fact`, `facts_about`, `record_qa`, `save_report`, …) and
pydantic validation. Multi-tenant is reachable by adding `users/<other>/` — the
default-user resolution is the only single-tenant assumption, and it is isolated.

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
