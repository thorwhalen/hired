"""Refresh bookkeeping: per-source content digests + last-refresh timestamps.

Records a content digest for every raw source the candidate has provided, so a
later refresh can tell which sources are *new* or *changed* since they were last
ingested — without re-reading everything. The state is a singleton persisted at
``user/info/state.json`` and is the shared substrate for raw-source tracking
(:meth:`~hired.candidate.knowledge_base.CandidateKnowledgeBase.add_source`) and
the soft/hard refresh loop.
"""

from __future__ import annotations

import hashlib

from pydantic import BaseModel, Field

from hired.candidate.base import _utcnow


def sha256_hex(data: bytes) -> str:
    """Content hash used as the change signal for a raw source."""
    return hashlib.sha256(data).hexdigest()


class SourceDigest(BaseModel):
    """What we know about one raw source for change detection + provenance."""

    key: str  # the source's key in the raw store (its filename)
    sha256: str
    size: int
    added_at: str = Field(default_factory=_utcnow)
    ingested_at: str | None = None  # set when facts were last derived from it
    fact_ids: list[str] = Field(default_factory=list)  # facts derived from it


class RefreshState(BaseModel):
    """The candidate-info refresh ledger (persisted to ``user/info/state.json``)."""

    last_soft_refresh: str | None = None
    last_hard_refresh: str | None = None
    sources: dict[str, SourceDigest] = Field(default_factory=dict)


def load_state(user_store) -> RefreshState:
    """Read the refresh state for a :class:`UserStore` (empty if none yet)."""
    raw = user_store.read_state()
    return RefreshState.model_validate(raw) if raw else RefreshState()


def save_state(user_store, state: RefreshState) -> None:
    """Persist the refresh state for a :class:`UserStore`."""
    user_store.write_state(state.model_dump(mode="json"))
