"""Soft/hard refresh of the candidate's ``info`` from changed sources + new Q&A.

The package provides the **deterministic mechanism** — detect what changed (via the
per-source digests in ``state.json``), drive (re)extraction through an injected
``ingest_fn``, apply the results (supersede stale source-derived facts, add fresh
ones, update the ledger, regenerate the synopsis) — while the **intelligence**
(actually reading a document/answer and proposing atomic facts) stays external, so
the import-safety contract holds. A skill or an injected LLM supplies ``ingest_fn``.

Two modes:

- **soft** (default): only *new or changed* sources, plus Q&A entries not yet
  distilled, are (re)read. A changed source's prior facts are superseded; a new
  source's facts are simply added.
- **hard**: *every* source is re-derived from scratch and reconciled by superseding
  the facts previously derived from each source. Use for a periodic rebuild.

Pass ``apply=False`` to get a non-destructive :class:`RefreshReport` of what *would*
change (proposals) so the candidate can validate before anything is written.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from hired.candidate.base import FactStatus, SourceKind, _utcnow
from hired.candidate.ingest import ingest_facts
from hired.candidate.state import SourceDigest, load_state, save_state, sha256_hex

SOURCE = "source"
QA = "qa"


@dataclass
class RefreshItem:
    """One unit of pending work for a refresh: a changed source or an undistilled Q&A."""

    kind: str  # SOURCE | QA
    key: str  # source filename or qa id
    content: bytes | str  # raw bytes (source) or answer text (qa)


@dataclass
class RefreshProposal:
    """Proposed fact records for one item (returned when ``apply=False``)."""

    kind: str
    key: str
    records: list[dict]


@dataclass
class RefreshReport:
    """Outcome (or preview) of a refresh."""

    mode: str
    applied: bool
    pending: list[RefreshItem] = field(default_factory=list)
    proposals: list[RefreshProposal] = field(default_factory=list)
    added_fact_ids: list[str] = field(default_factory=list)
    superseded_fact_ids: list[str] = field(default_factory=list)

    def summary(self) -> str:
        if self.applied:
            return (
                f"{self.mode} refresh: +{len(self.added_fact_ids)} facts, "
                f"superseded {len(self.superseded_fact_ids)}, "
                f"from {len(self.pending)} item(s)"
            )
        return (
            f"{self.mode} refresh (preview): {len(self.proposals)} proposal(s) "
            f"across {len(self.pending)} pending item(s) — nothing written"
        )


def _as_text(content: bytes | str) -> str | None:
    """Best-effort text for the quote invariant (None if not decodable)."""
    if isinstance(content, str):
        return content
    try:
        return content.decode("utf-8")
    except UnicodeDecodeError:
        return None


def pending_sources(kb) -> list[str]:
    """Raw source keys that are new, changed, or never ingested into facts."""
    state = load_state(kb._store)
    out: list[str] = []
    for key in kb.sources():
        digest = state.sources.get(key)
        if digest is None or digest.ingested_at is None:
            out.append(key)  # never recorded, or recorded but never ingested
        elif sha256_hex(kb.get_source(key)) != digest.sha256:
            out.append(key)  # content changed since last ingest
    return sorted(out)


def pending_qa(kb) -> list:
    """Q&A entries not yet distilled into facts (no ``derived_fact_ids``)."""
    return [q for q in kb.qa_entries() if not q.derived_fact_ids]


def needs_refresh(kb) -> bool:
    """True when there is uningested source/Q&A material — a refresh is warranted."""
    return bool(pending_sources(kb)) or bool(pending_qa(kb))


def _collect(kb, mode: str) -> list[RefreshItem]:
    if mode == "hard":
        source_keys = sorted(kb.sources())
    elif mode == "soft":
        source_keys = pending_sources(kb)
    else:
        raise ValueError(f"mode must be 'soft' or 'hard', got {mode!r}")
    items = [RefreshItem(SOURCE, k, kb.get_source(k)) for k in source_keys]
    items += [RefreshItem(QA, q.id, q.answer) for q in pending_qa(kb)]
    return items


def _supersede(kb, fact_ids: list[str]) -> list[str]:
    """Mark the given (still-asserted) facts superseded; return those changed."""
    changed: list[str] = []
    for fid in fact_ids:
        try:
            fact = kb.get_fact(fid)
        except KeyError:
            continue
        if fact.status == FactStatus.ASSERTED:
            fact.status = FactStatus.SUPERSEDED
            fact.updated_at = _utcnow()
            kb._facts[fid] = fact
            changed.append(fid)
    return changed


def refresh(
    kb, mode: str = "soft", *, ingest_fn=None, apply: bool = True
) -> RefreshReport:
    """Refresh ``info`` from changed sources + undistilled Q&A. See module docstring.

    ``ingest_fn(item: RefreshItem) -> list[dict]`` supplies the extraction
    intelligence (records are the usual ``{"statement", "category", "quote", …}``
    dicts). With ``ingest_fn=None`` the report just lists the pending items (the
    caller does extraction). With ``apply=False`` the records are returned as
    proposals and nothing is written.
    """
    items = _collect(kb, mode)
    report = RefreshReport(
        mode=mode, applied=apply and ingest_fn is not None, pending=items
    )

    if ingest_fn is None:
        return report  # discovery only; caller will extract

    state = load_state(kb._store)
    for item in items:
        records = ingest_fn(item) or []
        if not apply:
            report.proposals.append(RefreshProposal(item.kind, item.key, records))
            continue
        if item.kind == SOURCE:
            prior = state.sources.get(item.key)
            if (
                prior and prior.fact_ids
            ):  # changed/hard re-derive → supersede stale facts
                report.superseded_fact_ids += _supersede(kb, prior.fact_ids)
            new_ids = ingest_facts(
                kb,
                records,
                source_kind=SourceKind.UPLOAD,
                source_id=item.key,
                source_text=_as_text(item.content),
            )
            report.added_fact_ids += new_ids
            data = (
                item.content
                if isinstance(item.content, bytes)
                else item.content.encode()
            )
            state.sources[item.key] = SourceDigest(
                key=item.key,
                sha256=sha256_hex(data),
                size=len(data),
                ingested_at=_utcnow(),
                fact_ids=new_ids,
            )
        else:  # QA
            new_ids = ingest_facts(
                kb,
                records,
                source_kind=SourceKind.QA,
                source_id=item.key,
                source_text=_as_text(item.content),
            )
            report.added_fact_ids += new_ids
            _backlink_qa(kb, item.key, new_ids)

    if report.applied:
        stamp = _utcnow()
        if mode == "hard":
            state.last_hard_refresh = stamp
        state.last_soft_refresh = stamp
        save_state(kb._store, state)
        kb.regenerate_synopsis()
    return report


def _backlink_qa(kb, qa_id: str, fact_ids: list[str]) -> None:
    """Record derived fact ids on the Q&A entry so its answer stays discoverable."""
    for entry in kb.qa_entries():
        if entry.id == qa_id:
            entry.derived_fact_ids = list(entry.derived_fact_ids) + fact_ids
            kb._qa[qa_id] = entry
            return
