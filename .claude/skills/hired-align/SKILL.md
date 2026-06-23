---
name: hired-align
description: Use to analyze how well a candidate fits a job description and to accumulate reusable knowledge about the candidate. Triggers on "analyze this JD against my profile", "how well do I match this job", "what are my gaps for this role", "help me respond to a recruiter about this job", "align my profile to this job description", or when given one or more JDs to assess for a candidate. Classifies each requirement into strong-match / adjacent-transferable / gap-learnable / gap-hard, asks clarifying questions instead of assuming gaps, and persists everything (facts + Q&A + reports) outside the repo under ~/.local/share/hired/.
---

# hired-align — honest JD ↔ candidate alignment

Analyze a job description against an accumulating **candidate knowledge base**,
classify each requirement honestly, ask the candidate about what you *don't know*
(never assume a gap from silence), and persist everything for reuse across jobs.

Architecture, schemas, and rubric: **`misc/docs/DESIGN.md`**. You (the agent) are
the *intelligence*; the `hired` package provides storage, schemas, the
deterministic rubric, and report rendering.

## Non-negotiable rules

1. **Never exaggerate.** A match needs grounding evidence (a fact with a quote, or
   the candidate's own answer). No evidence → it is not a strong match.
2. **`UNKNOWN` ≠ absent.** If the knowledge base doesn't address a requirement,
   it is `UNKNOWN` — a *question to ask the candidate*, not a gap. Only an explicit
   negative (the candidate said "no") or a missing **closed-field** item
   (e.g. a required degree they haven't got) is a real gap.
3. **AI-leverage is real.** The candidate works with armies of AI agents offline.
   For *codified / knowledge-breadth* gaps this materially lowers ramp time → set
   `ai_leverage` and let the rubric soften the bucket. It does **not** rescue
   *tacit-judgment* or *enduring-aptitude* gaps.
4. **Privacy.** All candidate data, Q&A, JDs, and reports persist **only** under
   `~/.local/share/hired/` (or `$HIRED_DATA_DIR`). Never write them into the repo
   or a commit.

## Setup — two levels: the candidate, and the engagement

Knowledge about the **candidate** (facts, Q&A, synopsis, raw sources) is reusable
across every job and lives at the user level (`kb`). Work on **one company's
role(s)** (parsed jobs, alignment reports, company research, interview prep) lives
in a per-engagement **workspace** (`ws = kb.jd(jd_id, ...)`).

```python
from hired.candidate import CandidateKnowledgeBase
kb = CandidateKnowledgeBase()                     # default candidate "me" (user-level)
print(kb.synopsis)                                # fast context load of what's already known

ws = kb.jd(jd_id, company="<Company>", label="<short label>")  # the engagement
```

`jd_id` is a slug for the engagement — **one or a group of related roles at the
same company**, usually the company slug (e.g. `"socure"`). If the candidate gives
you several unrelated roles at one big company and wants them separate, use distinct
`jd_id`s. A single role's alignment report is keyed by `job_id` *within* `ws`.

## Step 1 — Ingest the candidate profile (once, then incrementally)

If there are new raw documents (CVs, bios, publications), delegate extraction to
the **`hired-profile-ingest`** subagent (it reads the files and returns atomic
fact records). Then persist them:

```python
from hired.candidate import SourceKind
from hired.candidate.ingest import ingest_facts
ingest_facts(kb, fact_records, source_kind=SourceKind.UPLOAD,
             source_id="Thor_CV.pdf", source_text=raw_text)  # quote invariant enforced
kb.regenerate_synopsis()
```

Records are `{"statement","category","tags","confidence","quote","locator","is_negation"}`.
Keep statements **atomic** (one claim each). Quotes MUST be verbatim substrings of
the source (the package drops quotes that aren't).

## Step 2 — Analyze a JD

1. Save the JD into the engagement (`ws.save_job(job_id, {...})`) and decompose it
   into atomic `Requirement`s (verbatim `text`), tagging each `requirement_class`
   (gate_keeper / differentiator / value_add), `skill_type`, and `required_level` (0–5).
2. For each requirement, gather evidence from the KB (`kb.facts(...)`, the synopsis)
   and build a `RequirementRecord`: set `match_state`
   (CONFIRMED / CONTRADICTED / UNKNOWN), `match_type` (direct / adjacent / none),
   `candidate_level`, `evidence` (with a quote), `confidence`, and — for gaps —
   `closeability`, `time_to_close`, and `ai_leverage`.
3. Run the deterministic rubric to assign buckets:

```python
from hired.alignment import classify
for rec in records:
    classify(rec)            # fills gap_size, bucket, needs_clarification
```

Use the `hired-requirement-analyst` subagent to classify many requirements in
parallel when a JD is large.

## Step 3 — Elicitation loop (the honesty engine)

```python
from hired.alignment import rank_clarifications, is_decision_stable
clarifs = rank_clarifications(records, max_questions=6)   # highest info-gain first
```

Ask the candidate these questions (draft the actual `question` text; the helper
ranks the *unknowns*). Prefer batching with the AskUserQuestion tool. For each
answer:

- record it: `kb.record_qa(QAEntry(question=..., answer=..., asked_for_job=job_id))`;
- extract atomic facts from the answer and `ingest_facts(..., source_kind=SourceKind.QA)`;
- re-build/re-`classify()` the affected requirement(s) — verdicts may change.

Stop when `is_decision_stable(records)` is True, or you hit a sensible question
budget. Unresolved unknowns stay as open questions in the report (honest).

**After every Q&A batch, refresh the report.** A report generated before a Q&A
batch will carry false negatives the new answers resolve. Run the
`hired-alignment-review` subagent in **light mode** (read the existing report + the
new Q&A, propose targeted edits — typically `UNKNOWN → confirmed/adjacent` and
resolved clarifications), confirm the edits with the user, then persist. This keeps
`ws.save_report(...)` current (it archives the prior version automatically). For a
periodic deep audit, run the review in **heavy mode** (regenerate fresh via
`hired-alignment-report`, then diff).

## Step 4 — Report

Build an `AlignmentReport` (verdict-first; `bucket_counts`; `blocking_gaps`;
`next_actions`; `interview_prep` with bridge statements for transferable skills and
ramp plans for learnable gaps), render and persist it:

```python
from hired.alignment import render_report_markdown
md = render_report_markdown(report)
ws.save_report(job_id, report.model_dump(mode="json"))
```

Present the markdown to the user. For a recruiter response, lead with the strong
matches and transferable adjacencies, frame learnable gaps honestly (with the
AI-leverage ramp), and be candid about any hard gaps — truthful, not misleading,
but in the best positive light.

## The agent roster (reusable independently)

- **`hired-profile-ingest`** — documents → atomic, quote-grounded facts.
- **`hired-requirement-analyst`** — classify one requirement vs evidence (parallelizable).
- **`hired-alignment-report`** — the canonical generator: all evidence → a full report,
  unanchored by any existing report. Use for a new JD or as heavy-review's fresh opinion.
- **`hired-alignment-review`** — light (patch false negatives from new Q&A) / heavy
  (regenerate + adversarial diff) report refresh; proposes, never auto-applies.
- **`hired-company-research`** — company + people research for interview prep.
- **`hired-interview-prep`** — gap-focused study briefings tying JD terminology to the
  candidate's own experience by analogy. (See the `hired-interview-prep` skill.)

## Reuse

The candidate KB persists across sessions and jobs. On the next JD, `kb.synopsis`
already carries everything learned, so you ask *fewer, sharper* questions over time.
Within an engagement, reports are versioned (`ws.report_versions(job_id)`); company
reports and interview-prep briefings persist alongside (`ws.companies()`,
`ws.briefings()`). List all engagements with `kb.jds()`.
