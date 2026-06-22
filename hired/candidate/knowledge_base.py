"""The candidate knowledge base: a facade over the per-candidate store mall.

:class:`CandidateKnowledgeBase` is the domain-driven entry point for accumulating
and querying knowledge about one candidate. It wraps the :class:`CandidateMall`
stores with validated, intention-revealing methods (``add_fact``, ``facts``,
``record_qa``, ``save_upload``, …) and keeps a regenerated, human-readable
:meth:`synopsis` projection of the fact store for fast context loading.
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
from hired.persistence.base import DFLT_USER, CandidateMall
from hired.persistence.repository import Repository


class _FactRepo(Repository[Fact]):
    model = Fact


class _QARepo(Repository[QAEntry]):
    model = QAEntry


class CandidateKnowledgeBase:
    """Accumulated, open-world knowledge about a single candidate.

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

    def __init__(self, user: str = DFLT_USER, *, mall: CandidateMall | None = None):
        self.user = user
        self.mall = mall or CandidateMall(user)
        self._facts = _FactRepo(self.mall['facts'])
        self._qa = _QARepo(self.mall['qa'])

    # --- facts -------------------------------------------------------------
    def add_fact(self, fact: Fact) -> str:
        """Persist a fact, returning its id."""
        return self._facts.add(fact)

    def add_facts(self, facts: 'Iterator[Fact] | list[Fact]') -> list[str]:
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

    # --- raw uploads -------------------------------------------------------
    def save_upload(self, name: str, data: bytes) -> None:
        """Store a raw uploaded document (CV, bio, publication) by filename."""
        self.mall['uploads'][name] = data

    def get_upload(self, name: str) -> bytes:
        return self.mall['uploads'][name]

    def uploads(self) -> list[str]:
        return list(self.mall['uploads'])

    # --- jobs & reports (keyed by job id) ----------------------------------
    def save_job(self, job_id: str, data: dict) -> None:
        self.mall['jobs'][job_id] = data

    def get_job(self, job_id: str) -> dict:
        return self.mall['jobs'][job_id]

    def jobs(self) -> list[str]:
        return list(self.mall['jobs'])

    def save_report(self, job_id: str, data: dict) -> None:
        self.mall['reports'][job_id] = data

    def get_report(self, job_id: str) -> dict:
        return self.mall['reports'][job_id]

    # --- synopsis (regenerated projection) ---------------------------------
    def regenerate_synopsis(self) -> str:
        """Rebuild and persist a human-readable synopsis from current facts.

        This is a *projection* — always derived from the fact store, never
        hand-edited — so it can be regenerated at any time without loss.
        """
        by_cat: dict[str, list[str]] = {}
        for fact in self.facts():
            marker = 'NOT: ' if fact.is_negation else ''
            by_cat.setdefault(fact.category.value, []).append(
                f'- {marker}{fact.statement}  ({fact.confidence.value})'
            )
        lines = [f'# Candidate synopsis: {self.user}', '']
        for cat in sorted(by_cat):
            lines.append(f'## {cat}')
            lines.extend(sorted(by_cat[cat]))
            lines.append('')
        text = '\n'.join(lines).rstrip() + '\n'
        self.mall['synopsis']['synopsis.md'] = text
        return text

    @property
    def synopsis(self) -> str:
        """The last persisted synopsis, regenerating it if absent."""
        store = self.mall['synopsis']
        if 'synopsis.md' in store:
            return store['synopsis.md']
        return self.regenerate_synopsis()
