# hired.alignment.assemble

Deterministically finalize an analyst-drafted `AlignmentReport`.

The *judgments* in a report (match state, levels, adjacency, closeability, the
verdict) come from outside the package — the `hired-align` skill or an injected
LLM. Everything that can be *derived* from those judgments is derived here, so a
report never carries stale bookkeeping after a record changes:

- every record is re-[`classify()`](hired.alignment.rubric.html.md#hired.alignment.rubric.classify)-ed (gap size, bucket,
  `needs_clarification`),
- `score_summary.bucket_counts` is recounted,
- `blocking_gaps` is rebuilt from the current records,
- `clarifications` is re-ranked by info gain (keeping any question text the
  analyst already drafted, dropping those whose requirement is now resolved),
- `verdict.has_blocking_gaps` and `created_at` are filled in.

This is what the `hired analyze` CLI command runs before persisting a report.

### Functions

| [`finalize_report`](#hired.alignment.assemble.finalize_report)(report)   | Return a copy of `report` with every derivable field recomputed.       |
|----------------------------------------------------------------------------|------------------------------------------------------------------------|
| [`is_blocking`](#hired.alignment.assemble.is_blocking)(record)       | True for a gate-keeper requirement that is a hard gap or contradicted. |

### hired.alignment.assemble.finalize_report(report)

Return a copy of `report` with every derivable field recomputed.

Clarifications and flagged blockers refer to requirements by `id`; give
requirements explicit ids in a draft so those links survive (flagged
blockers also fall back to matching by requirement text).

```pycon
>>> from hired.alignment import (AlignmentReport, Requirement, RequirementRecord,
...     RequirementClass, Verdict, Recommendation, MatchType, Closeability)
>>> from hired.candidate.base import MatchState
>>> gate = Requirement(id='r1', text='PhD', requirement_class=RequirementClass.GATE_KEEPER)
>>> recs = [
...     RequirementRecord(requirement=gate, closeability=Closeability.STRUCTURALLY_HARD,
...                       match_state=MatchState.CONTRADICTED),
...     RequirementRecord(requirement=Requirement(id='r2', text='Python', required_level=3),
...                       match_state=MatchState.CONFIRMED, match_type=MatchType.DIRECT,
...                       candidate_level=5),
... ]
>>> report = finalize_report(AlignmentReport(
...     job_id='ds', verdict=Verdict(recommendation=Recommendation.STRETCH),
...     requirements=recs))
>>> report.score_summary.bucket_counts['strong_match']
1
>>> [r.requirement.id for r in report.blocking_gaps], report.verdict.has_blocking_gaps
(['r1'], True)
```

* **Return type:**
  [`AlignmentReport`](hired.alignment.base.html.md#hired.alignment.base.AlignmentReport)

### hired.alignment.assemble.is_blocking(record)

True for a gate-keeper requirement that is a hard gap or contradicted.

* **Return type:**
  [`bool`](https://docs.python.org/3/builtins/functions.html#bool)
