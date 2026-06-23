"""Candidate knowledge domain: accumulate open-world facts about a candidate.

The public facade is :class:`CandidateKnowledgeBase`. Schemas (:class:`Fact`,
:class:`QAEntry`, :class:`Provenance`, and the enums) live in
:mod:`hired.candidate.base`; document/Q&A ingest in :mod:`hired.candidate.ingest`.

See ``misc/docs/DESIGN.md`` §5.
"""

from hired.candidate.base import (
    ConfidenceLevel,
    Fact,
    FactCategory,
    FactStatus,
    MatchState,
    Provenance,
    QAEntry,
    SourceKind,
)
from hired.candidate.knowledge_base import CandidateKnowledgeBase
from hired.candidate.ingest import ingest_facts, fact_from_record, verify_quote

__all__ = [
    'CandidateKnowledgeBase',
    'Fact',
    'QAEntry',
    'Provenance',
    'FactCategory',
    'FactStatus',
    'SourceKind',
    'ConfidenceLevel',
    'MatchState',
    'ingest_facts',
    'fact_from_record',
    'verify_quote',
]
