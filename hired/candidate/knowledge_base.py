"""The candidate knowledge base: a facade over the user-level store.

:class:`CandidateKnowledgeBase` is the domain-driven entry point for accumulating
and querying knowledge about one candidate — *what is true about them*, reusable
across every job application. It wraps the :class:`~hired.persistence.base.UserStore`
with validated, intention-revealing methods (``add_fact``, ``facts``, ``record_qa``,
``save_upload``, …) and keeps a regenerated, human-readable :meth:`synopsis`
projection of the fact store for fast context loading.

Work tied to a specific company's role(s) — alignment reports, company research,
interview prep — does **not** live here; it lives in a per-engagement
:class:`~hired.candidate.workspace.JDWorkspace`, reached via :meth:`jd`.
"""

from __future__ import annotations

from collections.abc import Iterator

from hired.candidate.base import (
    Fact,
    FactCategory,
    FactStatus,
    QAEntry,
    _utcnow,
)
from hired.candidate.workspace import JDWorkspace
from hired.persistence.base import DFLT_USER, UserStore, list_jds
from hired.persistence.migrate import ensure_v2
from hired.persistence.repository import Repository


class _FactRepo(Repository[Fact]):
    model = Fact


class _QARepo(Repository[QAEntry]):
    model = QAEntry


class CandidateKnowledgeBase:
    """Accumulated, open-world knowledge about a single candidate (user-level).

    >>> import tempfile, os
    >>> os.environ['HIRED_DATA_DIR'] = tempfile.mkdtemp()
    >>> kb = CandidateKnowledgeBase()                 # default candidate "me"
    >>> from hired.candidate.base import Fact, FactCategory
    >>> _ = kb.add_fact(Fact(statement='Built ML pipelines in Python',
    ...                       category=FactCategory.SKILL, tags=['python', 'ml']))
    >>> [f.statement for f in kb.facts(category=FactCategory.SKILL)]
    ['Built ML pipelines in Python']
    >>> [f.statement for f in kb.facts(tags=['ml'])]
    ['Built ML pipelines in Python']
    """

    def __init__(self, user: str = DFLT_USER, *, store: UserStore | None = None):
        self.user = user
        # Auto-migrate a legacy flat layout to v2 on first access (idempotent).
        ensure_v2(user, root=store._root if store is not None else None)
        self._store = store or UserStore(user)
        self._facts = _FactRepo(self._store.facts)
        self._qa = _QARepo(self._store.qa)

    # --- facts -------------------------------------------------------------
    def add_fact(self, fact: Fact) -> str:
        """Persist a fact, returning its id."""
        return self._facts.add(fact)

    def add_facts(self, facts: "Iterator[Fact] | list[Fact]") -> list[str]:
        return [self.add_fact(f) for f in facts]

    def get_fact(self, fact_id: str) -> Fact:
        return self._facts.get(fact_id)

    def facts(
        self,
        *,
        category: FactCategory | None = None,
        tags: list[str] | None = None,
        status: FactStatus | None = FactStatus.ASSERTED,
        include_negations: bool = True,
    ) -> Iterator[Fact]:
        """Iterate facts, optionally filtered by category/tags/status.

        By default only ``ASSERTED`` facts are returned (superseded ones are
        hidden). ``tags`` matches facts containing *any* of the given tags.
        """
        tagset = set(tags or [])
        for fact in self._facts.values():
            if status is not None and fact.status != status:
                continue
            if category is not None and fact.category != category:
                continue
            if tagset and not (tagset & set(fact.tags)):
                continue
            if not include_negations and fact.is_negation:
                continue
            yield fact

    def supersede(self, old_fact_id: str, new_fact: Fact) -> str:
        """Replace ``old_fact_id`` with ``new_fact`` (invalidate, don't delete)."""
        old = self._facts.get(old_fact_id)
        old.status = FactStatus.SUPERSEDED
        old.updated_at = _utcnow()
        self._facts[old_fact_id] = old
        new_fact.supersedes = old_fact_id
        return self._facts.add(new_fact)

    # --- Q&A ---------------------------------------------------------------
    def record_qa(self, entry: QAEntry) -> str:
        """Append a clarifying Q&A exchange to the (append-only) history."""
        return self._qa.add(entry)

    def qa_entries(self) -> Iterator[QAEntry]:
        return self._qa.values()

    # --- raw uploads / sources --------------------------------------------
    def save_upload(self, name: str, data: bytes) -> None:
        """Store a raw uploaded document (CV, bio, publication) by filename."""
        self._store.raw[name] = data

    def get_upload(self, name: str) -> bytes:
        return self._store.raw[name]

    def uploads(self) -> list[str]:
        return list(self._store.raw)

    # --- engagements (per-JD workspaces) -----------------------------------
    def jd(
        self, jd_id: str, *, company: str | None = None, label: str | None = None
    ) -> JDWorkspace:
        """Get-or-create the workspace for an engagement (1+ JDs of one company).

        ``company`` / ``label`` are recorded in the engagement's ``meta`` when given.
        """
        ws = JDWorkspace(self, jd_id)
        if company is not None or label is not None:
            ws.set_meta(jd_id=jd_id, company=company, label=label)
        return ws

    def jds(self) -> list[str]:
        """Ids of all engagements for this candidate."""
        return list_jds(self.user, root=self._store._root)

    # --- synopsis (regenerated projection) ---------------------------------
    def regenerate_synopsis(self) -> str:
        """Rebuild and persist a human-readable synopsis from current facts.

        This is a *projection* — always derived from the fact store, never
        hand-edited — so it can be regenerated at any time without loss.
        """
        by_cat: dict[str, list[str]] = {}
        for fact in self.facts():
            marker = "NOT: " if fact.is_negation else ""
            by_cat.setdefault(fact.category.value, []).append(
                f"- {marker}{fact.statement}  ({fact.confidence.value})"
            )
        lines = [f"# Candidate synopsis: {self.user}", ""]
        for cat in sorted(by_cat):
            lines.append(f"## {cat}")
            lines.extend(sorted(by_cat[cat]))
            lines.append("")
        text = "\n".join(lines).rstrip() + "\n"
        self._store.write_synopsis(text)
        return text

    @property
    def synopsis(self) -> str:
        """The last persisted synopsis, regenerating it if absent."""
        text = self._store.read_synopsis()
        return text if text is not None else self.regenerate_synopsis()
