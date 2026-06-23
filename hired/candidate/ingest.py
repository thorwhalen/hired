"""Turn extracted atomic-fact records into persisted, provenance-bearing facts.

The *intelligence* of extraction (reading a CV/bio/publication and proposing
atomic claims) is supplied externally — by the ``hired-profile-ingest`` subagent
in interactive use, or an injected LLM in autonomous use. This module is the
deterministic glue: it validates those proposals into :class:`Fact` objects,
enforces the provenance-quote invariant, and persists them.

A *record* is a lightweight dict:

```
{"statement": "...", "category": "skill", "tags": ["python"],
 "confidence": "high", "quote": "...", "locator": "experience[1]",
 "is_negation": false}
```
"""

from __future__ import annotations

from hired.candidate.base import (
    ConfidenceLevel,
    Fact,
    FactCategory,
    Provenance,
    SourceKind,
)
from hired.candidate.knowledge_base import CandidateKnowledgeBase


def verify_quote(quote: str | None, source_text: str | None) -> bool:
    """True if ``quote`` is a verbatim substring of ``source_text``.

    A ``None`` quote (no quote claimed) always verifies. When no source text is
    available to check against, we cannot disprove it, so it verifies too — the
    invariant only bites when we *can* check.
    """
    if not quote or source_text is None:
        return True
    return _normalize(quote) in _normalize(source_text)


def _normalize(s: str) -> str:
    return " ".join(s.split()).lower()


def fact_from_record(
    record: dict,
    *,
    source_kind: SourceKind,
    source_id: str = "",
    subject: str = "me",
) -> Fact:
    """Build a (not-yet-persisted) :class:`Fact` from a record dict."""
    quote = record.get("quote")
    prov = Provenance(
        source_kind=source_kind,
        source_id=record.get("source_id", source_id),
        locator=record.get("locator", ""),
        quote=quote,
    )
    return Fact(
        subject=subject,
        category=FactCategory(record.get("category", "other")),
        statement=record["statement"],
        value=record.get("value"),
        confidence=ConfidenceLevel(record.get("confidence", "medium")),
        is_negation=bool(record.get("is_negation", False)),
        provenance=[prov],
        tags=list(record.get("tags", [])),
    )


def ingest_facts(
    kb: CandidateKnowledgeBase,
    records: list[dict],
    *,
    source_kind: SourceKind,
    source_id: str = "",
    source_text: str | None = None,
    drop_unverified_quotes: bool = True,
) -> list[str]:
    """Validate, quote-check, and persist fact records; return persisted ids.

    When ``source_text`` is given, each record's ``quote`` is checked to be a
    verbatim substring. Unverified quotes are dropped (the fact is still kept,
    but without the spurious quote) unless ``drop_unverified_quotes`` is False,
    in which case a ``ValueError`` is raised — useful for strict pipelines.
    """
    ids: list[str] = []
    for record in records:
        if not verify_quote(record.get("quote"), source_text):
            if drop_unverified_quotes:
                record = {**record, "quote": None}
            else:
                raise ValueError(
                    f"Quote not found verbatim in source: {record.get('quote')!r}"
                )
        fact = fact_from_record(record, source_kind=source_kind, source_id=source_id)
        ids.append(kb.add_fact(fact))
    return ids
