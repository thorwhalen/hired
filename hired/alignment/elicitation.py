"""The honesty loop: rank unknowns into the most informative questions first.

This module is deterministic scaffolding around a judgment the analyst makes.
It computes which ``UNKNOWN`` requirements are worth asking about, in what order
(by expected information gain ≈ profile-uncertainty × requirement-criticality),
and whether the analysis has become *decision-stable* enough to stop.

See ``misc/docs/DESIGN.md`` §8.
"""

from __future__ import annotations

from hired.alignment.base import (
    Clarification,
    Decision,
    FieldCompleteness,
    RequirementClass,
    RequirementRecord,
)
from hired.candidate.base import ConfidenceLevel, MatchState

# How decision-critical each requirement class is (the "criticality" factor).
_CRITICALITY = {
    RequirementClass.GATE_KEEPER: 1.0,
    RequirementClass.DIFFERENTIATOR: 0.6,
    RequirementClass.VALUE_ADD: 0.25,
}

# How uncertain we are, by confidence level (the "uncertainty" factor).
_UNCERTAINTY = {
    ConfidenceLevel.LOW: 1.0,
    ConfidenceLevel.MEDIUM: 0.5,
    ConfidenceLevel.HIGH: 0.15,
}


def info_gain(record: RequirementRecord) -> float:
    """Expected information gain of resolving this requirement, wrt the verdict.

    Heuristic: ``uncertainty × criticality``. An ``impact`` override (1-5) scales
    criticality when the analyst has a sharper view than the requirement class.
    """
    uncertainty = _UNCERTAINTY[record.confidence]
    criticality = _CRITICALITY[record.requirement.requirement_class]
    impact_scale = record.impact / 3.0  # 3 is neutral
    return round(uncertainty * criticality * impact_scale, 4)


def is_decision_relevant(record: RequirementRecord) -> bool:
    """A requirement is worth asking about only if resolving it could move the
    verdict — i.e. it's not a low-value-add nice-to-have we can ignore."""
    return record.requirement.requirement_class != RequirementClass.VALUE_ADD


def should_ask(record: RequirementRecord) -> bool:
    """Whether to route this record to a clarifying question.

    Ask only when it's ``UNKNOWN`` on an OPEN field and decision-relevant — the
    "don't assume absence from silence" rule. CONTRADICTED facts and closed-field
    unknowns are real gaps, not questions. A decision-relevant CONFIRMED or
    CONTRADICTED record whose calibrated decision is *ask* (sampled judgments too
    inconsistent for the conformal rule, see :mod:`hired.alignment.calibration`)
    is asked about too: "never exaggerate" means a shaky match is confirmed first,
    and a shaky absence is not assumed. An UNKNOWN follows the rule above.
    """
    if not is_decision_relevant(record):
        return False
    if record.calibrated_decision == Decision.ASK and record.match_state != MatchState.UNKNOWN:
        return True
    return (
        record.match_state == MatchState.UNKNOWN
        and record.field_completeness == FieldCompleteness.OPEN
    )


def rank_clarifications(
    records: list[RequirementRecord],
    *,
    max_questions: int | None = None,
    min_info_gain: float = 0.0,
) -> list[Clarification]:
    """Produce clarifying questions for askable records, highest info-gain first.

    The question *text* is left to the analyst; this returns the prioritized
    skeleton (requirement, reason, info_gain) so the caller can fill ``question``.
    """
    askable = [r for r in records if should_ask(r)]
    for r in askable:
        r.info_gain = info_gain(r)
    askable.sort(key=lambda r: r.info_gain, reverse=True)
    out: list[Clarification] = []
    for r in askable:
        if r.info_gain < min_info_gain:
            continue
        out.append(
            Clarification(
                requirement_id=r.requirement.id,
                question="",  # filled by the analyst
                reason=f"{r.requirement.requirement_class.value} requirement is "
                + ("unknown" if r.match_state == MatchState.UNKNOWN
                   else "too uncertain to decide (calibrated)")
                + "; resolving it could move the verdict",
                info_gain=r.info_gain,
            )
        )
        if max_questions is not None and len(out) >= max_questions:
            break
    return out


def is_decision_stable(records: list[RequirementRecord]) -> bool:
    """True when no remaining open unknown could flip the verdict.

    Concretely: there are no askable (decision-relevant, open, unknown)
    requirements left. This is the sharpest stop criterion from the research.
    """
    return not any(should_ask(r) for r in records)
