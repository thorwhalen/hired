"""Deterministically finalize an analyst-drafted :class:`AlignmentReport`.

The *judgments* in a report (match state, levels, adjacency, closeability, the
verdict) come from outside the package — the ``hired-align`` skill or an injected
LLM. Everything that can be *derived* from those judgments is derived here, so a
report never carries stale bookkeeping after a record changes:

- every record is re-:func:`~hired.alignment.rubric.classify`-ed (gap size, bucket,
  ``needs_clarification``),
- ``score_summary.bucket_counts`` is recounted,
- ``blocking_gaps`` is rebuilt from the current records,
- ``clarifications`` is re-ranked by info gain (keeping any question text the
  analyst already drafted, dropping those whose requirement is now resolved),
- ``verdict.has_blocking_gaps`` and ``created_at`` are filled in.

This is what the ``hired analyze`` CLI command runs before persisting a report.
"""

from __future__ import annotations

from typing import Any

from hired.alignment.base import (
    AlignmentReport,
    Bucket,
    Clarification,
    RequirementClass,
    RequirementRecord,
)
from hired.alignment.elicitation import rank_clarifications
from hired.alignment.rubric import classify
from hired.candidate.base import MatchState, _utcnow

_GAP_BUCKETS = (Bucket.GAP_LEARNABLE, Bucket.GAP_HARD)


def is_blocking(record: RequirementRecord) -> bool:
    """True for a gate-keeper requirement that is a hard gap or contradicted."""
    return record.requirement.requirement_class == RequirementClass.GATE_KEEPER and (
        record.bucket == Bucket.GAP_HARD
        or record.match_state == MatchState.CONTRADICTED
    )


def _is_still_a_gap(record: RequirementRecord) -> bool:
    return (
        record.bucket in _GAP_BUCKETS or record.match_state == MatchState.CONTRADICTED
    )


def _blocking_gaps(
    records: list[RequirementRecord], flagged: list[RequirementRecord]
) -> list[RequirementRecord]:
    """Derived blockers plus analyst-flagged ones that are still gaps (current copies)."""
    flagged_ids = {r.requirement.id for r in flagged}
    return [
        r
        for r in records
        if is_blocking(r) or (r.requirement.id in flagged_ids and _is_still_a_gap(r))
    ]


def _merge_clarifications(
    records: list[RequirementRecord], drafted: list[Clarification]
) -> list[Clarification]:
    """Re-rank askable records; keep drafted question text for those still askable."""
    by_req = {c.requirement_id: c for c in drafted}
    merged = []
    for skeleton in rank_clarifications(records):
        prior = by_req.get(skeleton.requirement_id)
        if prior is not None:
            skeleton = prior.model_copy(update={"info_gain": skeleton.info_gain})
        merged.append(skeleton)
    return merged


def finalize_report(report: AlignmentReport | dict[str, Any]) -> AlignmentReport:
    """Return a copy of ``report`` with every derivable field recomputed.

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
    """
    report = AlignmentReport.model_validate(
        report.model_dump() if isinstance(report, AlignmentReport) else report
    )
    records = [classify(r) for r in report.requirements]
    report.requirements = records
    report.score_summary.bucket_counts = {
        b.value: sum(1 for r in records if r.bucket == b) for b in Bucket
    }
    report.blocking_gaps = _blocking_gaps(records, report.blocking_gaps)
    report.verdict.has_blocking_gaps = bool(report.blocking_gaps)
    report.clarifications = _merge_clarifications(records, report.clarifications)
    report.created_at = report.created_at or _utcnow()
    return report
