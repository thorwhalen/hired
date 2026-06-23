"""Schemas for JD-vs-candidate alignment analysis.

A job description is decomposed into :class:`Requirement` records; each is
analysed into a :class:`RequirementRecord` carrying a three-valued
:class:`~hired.candidate.base.MatchState`, a :class:`Bucket`, grounding
:class:`Evidence`, and the fields the elicitation loop needs. The whole analysis
is an :class:`AlignmentReport` — verdict-first, evidence-quoted, banded (never a
single false-precision percentage).

See ``misc/docs/DESIGN.md`` §6.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

from hired.candidate.base import ConfidenceLevel, MatchState, _new_id

# Re-export so callers can get the match-state enum from either domain.
__all_reexport__ = ['MatchState', 'ConfidenceLevel']


class Bucket(str, Enum):
    """The four alignment buckets."""

    STRONG_MATCH = 'strong_match'
    ADJACENT_TRANSFERABLE = 'adjacent_transferable'
    GAP_LEARNABLE = 'gap_learnable'
    GAP_HARD = 'gap_hard'


class MatchType(str, Enum):
    """How the candidate's background relates to the requirement (Axis A)."""

    DIRECT = 'direct'
    ADJACENT = 'adjacent'
    NONE = 'none'


class RequirementClass(str, Enum):
    """How decision-critical a requirement is."""

    GATE_KEEPER = 'gate_keeper'  # hard filter; failing it can block
    DIFFERENTIATOR = 'differentiator'  # strongly weighted
    VALUE_ADD = 'value_add'  # nice-to-have


class SkillType(str, Enum):
    TECHNICAL = 'technical'
    DOMAIN_KNOWLEDGE = 'domain_knowledge'
    SOFT_SKILL = 'soft_skill'
    CREDENTIAL = 'credential'


class Closeability(str, Enum):
    """How hard a gap is to close (Axis B), after the AI-leverage modifier."""

    QUICK_WIN = 'quick_win'
    LEARNABLE = 'learnable'
    REQUIRES_EXPERIENCE = 'requires_experience'
    STRUCTURALLY_HARD = 'structurally_hard'


class CloseMethod(str, Enum):
    COURSE = 'course'
    CERTIFICATION = 'certification'
    PRACTICE_PROJECT = 'practice_project'
    ON_THE_JOB = 'on_the_job'
    CREDENTIAL = 'credential'


class TimeToClose(str, Enum):
    DAYS = 'days'
    WEEKS = 'weeks'
    MONTHS = 'months'
    YEARS = 'years'


class Transferability(str, Enum):
    DIRECT = 'direct'
    CONTEXTUAL = 'contextual'
    FOUNDATIONAL = 'foundational'
    LIMITED = 'limited'


class AILeverage(str, Enum):
    """How much the candidate's standing AI-agent capability lowers the ramp.

    Applies to *codified / knowledge-breadth* gaps, not tacit-judgment or
    enduring-aptitude gaps (those it cannot rescue).
    """

    HIGH = 'high'
    MEDIUM = 'medium'
    LOW = 'low'
    NONE = 'none'


class FieldCompleteness(str, Enum):
    """Local closed-world flag: may a missing value be read as a real negative?"""

    OPEN = 'open'  # missing -> UNKNOWN (ask)
    CLOSED = 'closed'  # missing -> CONTRADICTED (sound to treat as absent)


class Recommendation(str, Enum):
    APPLY = 'apply'
    STRETCH = 'stretch'
    DO_NOT_APPLY = 'do_not_apply'


class FitBand(str, Enum):
    POOR = 'poor'
    WEAK = 'weak'
    FAIR = 'fair'
    GOOD = 'good'
    GREAT = 'great'


class Requirement(BaseModel):
    """One atomic requirement extracted verbatim from a job description."""

    id: str = Field(default_factory=lambda: _new_id('req-'))
    text: str  # verbatim from the JD
    skill_type: SkillType = SkillType.TECHNICAL
    requirement_class: RequirementClass = RequirementClass.DIFFERENTIATOR
    required_level: int = 3  # 0-5 (see DESIGN §6)


class Evidence(BaseModel):
    """A verbatim grounding span for a match judgment."""

    quote: str
    source_document_id: str = ''
    locator: str = ''


class RequirementRecord(BaseModel):
    """The analysis of one requirement against the candidate's knowledge."""

    requirement: Requirement

    # --- match state (the honesty core) -----------------------------------
    match_state: MatchState = MatchState.UNKNOWN
    field_completeness: FieldCompleteness = FieldCompleteness.OPEN
    bucket: Bucket | None = None  # None while UNKNOWN / unresolved
    match_type: MatchType = MatchType.NONE
    candidate_level: int = 0  # 0-5
    gap_size: int = 0  # max(required - candidate, 0)

    # --- adjacency (when match_type == ADJACENT) --------------------------
    source_skill: str | None = None
    adjacency_basis: str | None = None
    transferability: Transferability | None = None

    # --- closeability (gap buckets) ---------------------------------------
    closeability: Closeability | None = None
    close_method: CloseMethod | None = None
    time_to_close: TimeToClose | None = None
    ai_leverage: AILeverage = AILeverage.NONE

    # --- evidence + confidence (every record) -----------------------------
    confidence: ConfidenceLevel = ConfidenceLevel.LOW
    uncertainty_reason: str | None = None
    evidence: Evidence | None = None

    # --- prioritization + loop --------------------------------------------
    impact: int = 3  # 1-5 decision criticality
    info_gain: float = 0.0  # expected info gain wrt the verdict
    needs_clarification: bool = False
    talking_point: str | None = None


class Clarification(BaseModel):
    """A question to ask the candidate to resolve a decision-relevant unknown."""

    requirement_id: str
    question: str
    fills_field: str = ''  # which record field the answer would populate
    reason: str = ''
    info_gain: float = 0.0


class NextAction(BaseModel):
    action: str
    addresses: str = ''  # requirement id
    priority: int = 1
    expected_effect: str = ''


class Verdict(BaseModel):
    recommendation: Recommendation
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    confidence_basis: str = ''
    headline: str = ''
    key_reasons: list[str] = Field(default_factory=list)  # <= 5
    has_blocking_gaps: bool = False


class ScoreSummary(BaseModel):
    fit_band: FitBand = FitBand.FAIR
    bucket_counts: dict[str, int] = Field(default_factory=dict)
    ats_readability: float | None = None


class InterviewPrep(BaseModel):
    summary: str = ''
    talking_points: list[str] = Field(default_factory=list)
    story_library: list[dict] = Field(default_factory=list)  # STAR/CARLA stories
    proactive_disclosure: str = ''


class AlignmentReport(BaseModel):
    """A complete, verdict-first alignment analysis for one JD."""

    job_id: str
    job_title: str = ''
    company: str = ''
    created_at: str = ''
    verdict: Verdict
    score_summary: ScoreSummary = Field(default_factory=ScoreSummary)
    requirements: list[RequirementRecord] = Field(default_factory=list)
    blocking_gaps: list[RequirementRecord] = Field(default_factory=list)
    next_actions: list[NextAction] = Field(default_factory=list)
    interview_prep: InterviewPrep = Field(default_factory=InterviewPrep)
    clarifications: list[Clarification] = Field(default_factory=list)
