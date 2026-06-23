---
name: hired-interview-prep
description: Use to prepare a candidate for a headhunter call or company interview. Triggers on "prep me for the interview", "I have a call with the recruiter/headhunter", "help me get ready for the Socure interview", "what should I study before the interview", "research the company before I talk to them". Refreshes the alignment report from the latest Q&A, researches the company and people, and produces study briefings on the subjects/terminology the candidate is weakest on — each anchored by analogy to the candidate's own experience.
---

# hired-interview-prep

Get a candidate ready to speak fluently and position themselves honestly — for a
**headhunter** chat (broad fluency + framing) or a **company interview** (deeper
mechanism). Builds on the `hired-align` workflow and the candidate knowledge base.

## The flow

Work for one company lives in an **engagement workspace**: `ws = kb.jd(jd_id)`
(where `jd_id` is the engagement slug, usually the company — e.g. `"socure"`).
Reports, company research, and briefings are read/written through `ws`; the
candidate's cross-JD knowledge stays on `kb` (e.g. `kb.synopsis`).

1. **Refresh the alignment report first.** Interview prep must target the *current*
   gaps, and the report may predate recent Q&A. Run the **`hired-alignment-review`**
   subagent (light mode) for the job; confirm and apply any edits. Now the report's
   buckets reflect reality.

2. **Research the company (and people).** If there's no current company report
   (`ws.companies()`), run the **`hired-company-research`** subagent for the hiring
   company — business, market, recent news, the DS/AI org and named leaders, the
   recruiter/firm, likely interview focus, and candidate-specific talking points +
   questions to ask. Persisted via `ws.save_company_report(...)`.

3. **Produce study briefings.** Run the **`hired-interview-prep`** subagent. It reads
   the refreshed report + `kb.synopsis` + the company report and writes briefings
   focused on the candidate's weakest areas (`gap_hard`, `gap_learnable`, then
   `adjacent_transferable`), plus full JD-terminology coverage. **Every new concept is
   anchored to the candidate's own experience/jargon by analogy** (the anchor must be
   real, from the KB). Each briefing gives: what it is · your anchor · the bridge ·
   terminology to own · the honest one-liner. Persisted via `ws.save_briefing(...)`.

4. **Deliver** the company report + briefings, and a short "what to study, in order"
   summary. Calibrate depth to the occasion (headhunter vs technical interview).

## Principles

- **Target what they don't know**, but **teach it through what they do** — terminology
  sticks when it's "just X I already do, with new words."
- **Terminology fluency is the bar** — the candidate should not stumble on any JD term.
- **Honesty carries through** — briefings frame the candidate's real bridges and the
  residual ramps truthfully (same contract as `hired-align`).
- Persist everything (company report, briefings) so it's reusable and so the next
  prep starts from what's already known.
