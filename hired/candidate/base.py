"""Open-world, provenance-first schemas for accumulated candidate knowledge.

The governing principle (see ``misc/docs/DESIGN.md`` §5): the **absence** of a
fact is never a negative claim. Only an explicit fact whose ``match_state`` is
``CONTRADICTED`` asserts that the candidate lacks something. Silence is
``UNKNOWN`` — a prompt to *ask*, not a gap.

Every :class:`Fact` carries :class:`Provenance`. When a provenance ``quote`` is
drawn from a text source it MUST be a verbatim substring of that source — an
anti-hallucination invariant enforced at extraction time.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


def _new_id(prefix: str = '') -> str:
    return f'{prefix}{uuid.uuid4().hex[:12]}'


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class ConfidenceLevel(str, Enum):
    """Calibrated confidence in a claim (qualitative, not a raw probability)."""

    HIGH = 'high'
    MEDIUM = 'medium'
    LOW = 'low'


class MatchState(str, Enum):
    """Three-valued epistemic state — the core of the honesty contract.

    ``UNKNOWN`` is distinct from ``CONTRADICTED``: we have not yet looked, so we
    must *ask* rather than assume absence.
    """

    CONFIRMED = 'confirmed'
    CONTRADICTED = 'contradicted'
    UNKNOWN = 'unknown'


class FactStatus(str, Enum):
    """Whether a fact is current or has been superseded by a newer one."""

    ASSERTED = 'asserted'
    SUPERSEDED = 'superseded'


class FactCategory(str, Enum):
    """Coarse category for retrieval and synopsis grouping."""

    SKILL = 'skill'
    EXPERIENCE = 'experience'
    EDUCATION = 'education'
    ACHIEVEMENT = 'achievement'
    PREFERENCE = 'preference'
    CREDENTIAL = 'credential'
    TRAIT = 'trait'
    OTHER = 'other'


class SourceKind(str, Enum):
    """Where a piece of provenance came from."""

    UPLOAD = 'upload'
    QA = 'qa'
    INFERRED = 'inferred'
    EXTERNAL = 'external'


class Provenance(BaseModel):
    """Where a fact came from, with an optional verbatim supporting quote."""

    source_kind: SourceKind
    source_id: str = ''  # e.g. an upload filename or a qa entry id
    locator: str = ''  # e.g. "experience[2]" or "page 3"
    quote: str | None = None  # verbatim substring of the source when text
    captured_at: str = Field(default_factory=_utcnow)


class Fact(BaseModel):
    """One atomic claim about a candidate.

    Atomicity matters: a fact states a single thing so it can be confirmed,
    superseded, or cited independently.
    """

    id: str = Field(default_factory=lambda: _new_id('fact-'))
    subject: str = 'me'  # the candidate this is about (default tenant)
    category: FactCategory = FactCategory.OTHER
    statement: str  # atomic natural-language claim
    value: dict | list | str | float | int | bool | None = None  # optional payload
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    # When True, this fact asserts the candidate LACKS something (a real
    # negative), as opposed to mere silence. Drives CONTRADICTED downstream.
    is_negation: bool = False
    provenance: list[Provenance] = Field(default_factory=list)
    status: FactStatus = FactStatus.ASSERTED
    supersedes: str | None = None  # id of the fact this one replaces
    tags: list[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=_utcnow)
    updated_at: str = Field(default_factory=_utcnow)


class QAEntry(BaseModel):
    """One clarifying question asked of the candidate and their answer.

    Q&A is append-only history; the distilled, updatable projection lives in
    :class:`Fact` records (linked via ``derived_fact_ids``).
    """

    id: str = Field(default_factory=lambda: _new_id('qa-'))
    question: str
    answer: str
    asked_for_job: str | None = None  # job id that motivated the question
    fills_field: str | None = None  # which requirement field the answer informs
    derived_fact_ids: list[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=_utcnow)
