"""JD-vs-candidate alignment: classify each requirement honestly into four buckets.

Public surface:

- schemas in :mod:`hired.alignment.base` (:class:`Requirement`,
  :class:`RequirementRecord`, :class:`AlignmentReport`, and the enums),
- the deterministic rubric in :mod:`hired.alignment.rubric`
  (:func:`classify`, :func:`assign_bucket`, :func:`apply_ai_leverage`),
- the elicitation helpers in :mod:`hired.alignment.elicitation`
  (:func:`rank_clarifications`, :func:`is_decision_stable`),
- Markdown rendering in :mod:`hired.alignment.report`
  (:func:`render_report_markdown`).

The *intelligence* (judging transfer distance, trainability, evidence) is supplied
by the ``hired-align`` skill (Claude as brain) or an injected LLM; this package
provides the schemas, deterministic scoring, and rendering. See
``misc/docs/DESIGN.md`` §6-8.
"""

from hired.alignment.base import (
    AILeverage,
    AlignmentReport,
    Bucket,
    Clarification,
    Closeability,
    CloseMethod,
    Evidence,
    FieldCompleteness,
    FitBand,
    InterviewPrep,
    MatchType,
    NextAction,
    Recommendation,
    Requirement,
    RequirementClass,
    RequirementRecord,
    ScoreSummary,
    SkillType,
    TimeToClose,
    Transferability,
    Verdict,
)
from hired.alignment.rubric import (
    apply_ai_leverage,
    assign_bucket,
    classify,
    compute_gap_size,
)
from hired.alignment.elicitation import (
    info_gain,
    is_decision_stable,
    rank_clarifications,
    should_ask,
)
from hired.alignment.report import render_report_markdown
from hired.alignment.diff import diff_reports, summarize_diff

__all__ = [
    # schemas
    "Requirement",
    "RequirementRecord",
    "Evidence",
    "AlignmentReport",
    "Verdict",
    "ScoreSummary",
    "NextAction",
    "Clarification",
    "InterviewPrep",
    # enums
    "Bucket",
    "MatchType",
    "RequirementClass",
    "SkillType",
    "Closeability",
    "CloseMethod",
    "TimeToClose",
    "Transferability",
    "AILeverage",
    "FieldCompleteness",
    "Recommendation",
    "FitBand",
    # rubric
    "classify",
    "assign_bucket",
    "apply_ai_leverage",
    "compute_gap_size",
    # elicitation
    "rank_clarifications",
    "is_decision_stable",
    "should_ask",
    "info_gain",
    # report
    "render_report_markdown",
    # diff (used by the alignment-review refresh)
    "diff_reports",
    "summarize_diff",
]
