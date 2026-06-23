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
    slug,
)
from hired.candidate.knowledge_base import CandidateKnowledgeBase
from hired.candidate.workspace import JDWorkspace
from hired.candidate.topics import TopicDossier
from hired.candidate.state import RefreshState, SourceDigest
from hired.candidate.ingest import ingest_facts, fact_from_record, verify_quote

__all__ = [
    "CandidateKnowledgeBase",
    "JDWorkspace",
    "TopicDossier",
    "RefreshState",
    "SourceDigest",
    "Fact",
    "QAEntry",
    "Provenance",
    "FactCategory",
    "FactStatus",
    "SourceKind",
    "ConfidenceLevel",
    "MatchState",
    "slug",
    "ingest_facts",
    "fact_from_record",
    "verify_quote",
]
