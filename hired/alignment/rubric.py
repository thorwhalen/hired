"""Deterministic bucket assignment — the two-axis rubric in code.

The *judgment* (transfer distance, trainability, evidence) is supplied by the
analyst (Claude or an injected LLM). This module turns those judgments into a
:class:`~hired.alignment.base.Bucket` deterministically, so the classification is
auditable and reproducible. It also applies the **AI-leverage modifier**: a
candidate who works with armies of AI agents closes *codified / knowledge-breadth*
gaps faster — but not *tacit-judgment* or *enduring-aptitude* gaps.

See ``misc/docs/DESIGN.md`` §7.
"""

from __future__ import annotations

from hired.alignment.base import (
    AILeverage,
    Bucket,
    Closeability,
    FieldCompleteness,
    MatchType,
    RequirementRecord,
    SkillType,
)
from hired.candidate.base import MatchState


def compute_gap_size(required_level: int, candidate_level: int) -> int:
    """Residual gap, floored at zero."""
    return max(required_level - candidate_level, 0)


# Closeability levels that the AI-leverage modifier can soften, in order.
_SOFTENABLE = [
    Closeability.REQUIRES_EXPERIENCE,
    Closeability.LEARNABLE,
    Closeability.QUICK_WIN,
]


def apply_ai_leverage(
    closeability: Closeability,
    ai_leverage: AILeverage,
    *,
    skill_type: SkillType,
    is_tacit: bool = False,
) -> Closeability:
    """Soften a *codified* gap's closeability by the candidate's AI leverage.

    Tacit/soft gaps and structurally-hard gaps are never softened — AI agents
    extend *breadth of codified knowledge*, not judgment or enduring aptitude.

    >>> apply_ai_leverage(Closeability.REQUIRES_EXPERIENCE, AILeverage.HIGH,
    ...                    skill_type=SkillType.TECHNICAL)
    <Closeability.LEARNABLE: 'learnable'>
    >>> apply_ai_leverage(Closeability.REQUIRES_EXPERIENCE, AILeverage.HIGH,
    ...                    skill_type=SkillType.SOFT_SKILL)
    <Closeability.REQUIRES_EXPERIENCE: 'requires_experience'>
    """
    if is_tacit or skill_type == SkillType.SOFT_SKILL:
        return closeability
    if closeability == Closeability.STRUCTURALLY_HARD:
        return closeability  # genuinely hard (aptitude/credential) — unmoved
    steps = {
        AILeverage.HIGH: 1,
        AILeverage.MEDIUM: 1,
        AILeverage.LOW: 0,
        AILeverage.NONE: 0,
    }[ai_leverage]
    # MEDIUM only softens the already-learnable tiers, not requires_experience.
    if (
        ai_leverage == AILeverage.MEDIUM
        and closeability == Closeability.REQUIRES_EXPERIENCE
    ):
        steps = 0
    if steps == 0 or closeability not in _SOFTENABLE:
        return closeability
    idx = _SOFTENABLE.index(closeability)
    return _SOFTENABLE[min(idx + steps, len(_SOFTENABLE) - 1)]


def assign_bucket(record: RequirementRecord) -> Bucket | None:
    """Assign the alignment bucket for a record, or ``None`` if it should be a
    clarifying question instead.

    Returns ``None`` when the requirement is ``UNKNOWN`` on an OPEN field — that
    routes to elicitation rather than being scored as a gap (the "don't assume
    absence" rule). ``UNKNOWN`` on a CLOSED field is treated as a real gap.
    """
    state = record.match_state

    # UNKNOWN on an open field => not a bucket; ask the candidate.
    if (
        state == MatchState.UNKNOWN
        and record.field_completeness == FieldCompleteness.OPEN
    ):
        return None

    # Strong match: direct, and the candidate meets the required level.
    if (
        state == MatchState.CONFIRMED
        and record.match_type == MatchType.DIRECT
        and record.candidate_level >= record.requirement.required_level
    ):
        return Bucket.STRONG_MATCH

    # Adjacent/transferable: a related skill partially covers it.
    if record.match_type == MatchType.ADJACENT and state != MatchState.CONTRADICTED:
        # If the adjacent skill already meets the level, it's effectively strong.
        if (
            state == MatchState.CONFIRMED
            and record.candidate_level >= record.requirement.required_level
        ):
            return Bucket.STRONG_MATCH
        return Bucket.ADJACENT_TRANSFERABLE

    # Otherwise it's a gap; split by (AI-leverage-adjusted) closeability.
    closeability = record.closeability or Closeability.STRUCTURALLY_HARD
    closeability = apply_ai_leverage(
        closeability,
        record.ai_leverage,
        skill_type=record.requirement.skill_type,
    )
    if closeability in (Closeability.QUICK_WIN, Closeability.LEARNABLE):
        return Bucket.GAP_LEARNABLE
    return Bucket.GAP_HARD


def classify(record: RequirementRecord) -> RequirementRecord:
    """Fill ``gap_size`` and ``bucket`` (and ``needs_clarification``) in place.

    Returns the same record for convenience.
    """
    record.gap_size = compute_gap_size(
        record.requirement.required_level, record.candidate_level
    )
    bucket = assign_bucket(record)
    record.bucket = bucket
    record.needs_clarification = bucket is None
    return record
