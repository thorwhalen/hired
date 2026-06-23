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

import os
from collections.abc import Iterator
from pathlib import Path

from hired.candidate.base import (
    Fact,
    FactCategory,
    FactStatus,
    QAEntry,
    SourceKind,
    _new_id,
    _utcnow,
    slug,
)
from hired.candidate.ingest import ingest_facts
from hired.candidate.refresh import RefreshReport
from hired.candidate.refresh import needs_refresh as _needs_refresh
from hired.candidate.refresh import pending_qa as _pending_qa
from hired.candidate.refresh import pending_sources as _pending_sources
from hired.candidate.refresh import refresh as _refresh
from hired.candidate.state import SourceDigest, load_state, save_state, sha256_hex
from hired.candidate.topics import TopicDossier
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
    def record_qa(
        self, entry: QAEntry, *, derived_facts: "list[dict] | None" = None
    ) -> str:
        """Append a clarifying Q&A exchange; optionally distill it into facts.

        When ``derived_facts`` (atomic fact records extracted from the answer) are
        given, they are ingested with ``SourceKind.QA`` provenance (``source_id``
        = the Q&A id, quotes verified against the answer) and back-linked via the
        entry's ``derived_fact_ids`` — so a Q&A answer becomes reusable,
        discoverable knowledge rather than being buried in the history.
        """
        if derived_facts:
            ids = ingest_facts(
                self,
                derived_facts,
                source_kind=SourceKind.QA,
                source_id=entry.id,
                source_text=entry.answer,
            )
            entry.derived_fact_ids = list(entry.derived_fact_ids) + ids
        return self._qa.add(entry)

    def qa_entries(self) -> Iterator[QAEntry]:
        return self._qa.values()

    # --- raw sources (CVs, bios, publications, …) -------------------------
    def add_source(self, src: "str | Path | bytes", *, name: str | None = None) -> str:
        """Store a raw source (file path or bytes) and record its content digest.

        Returns the source key (its name in the raw store). The digest (in
        ``state.json``) lets a later refresh detect new/changed sources without
        re-reading everything. Facts extracted from a source cite it by this key.
        """
        if isinstance(src, (str, Path)) and os.path.isfile(str(src)):
            data = Path(src).read_bytes()
            name = name or os.path.basename(str(src))
        elif isinstance(src, (bytes, bytearray)):
            data = bytes(src)
            name = name or _new_id("src-")
        else:
            raise TypeError("add_source expects an existing file path or bytes")
        self._store.raw[name] = data
        state = load_state(self._store)
        # Record a digest only for a NEW source. For an existing one, leave the
        # prior digest intact: its sha256 still reflects the last *ingested*
        # content, so the now-differing bytes are detected as "changed" by
        # pending_sources(), and its fact_ids survive so a refresh can supersede
        # the stale facts. (A fresh source's ingested_at is None → also pending.)
        if name not in state.sources:
            state.sources[name] = SourceDigest(
                key=name, sha256=sha256_hex(data), size=len(data)
            )
            save_state(self._store, state)
        return name

    def get_source(self, name: str) -> bytes:
        return self._store.raw[name]

    def sources(self) -> list[str]:
        """Keys of all raw sources the candidate has provided."""
        return list(self._store.raw)

    # back-compat aliases for the pre-v2 upload API
    def save_upload(self, name: str, data: bytes) -> None:
        """Store a raw uploaded document by filename (see :meth:`add_source`)."""
        self.add_source(data, name=name)

    def get_upload(self, name: str) -> bytes:
        return self.get_source(name)

    def uploads(self) -> list[str]:
        return self.sources()

    # --- topic dossiers (volunteered, free-form knowledge by subject) ------
    def topic(self, name: str) -> TopicDossier:
        """Get-or-create the dossier for a subject (overview + optional files)."""
        return TopicDossier(self._store.topic_dir(slug(name)), name=name)

    def add_note(
        self, subject: str, text: str | None = None, *, files: "dict | None" = None
    ) -> TopicDossier:
        """Record volunteered info about a subject into its dossier.

        ``text`` is appended to the dossier's ``overview.md``; ``files`` (a
        ``{name: bytes}`` mapping) are attached as detail/media. Returns the
        dossier. This is the "by the way, I also did X" entry point — a single
        sentence or a whole folder both land here.
        """
        dossier = self.topic(subject)
        if text:
            dossier.add_note(text)
        for fname, data in (files or {}).items():
            dossier.add_file(fname, data)
        return dossier

    def topics(self) -> list[str]:
        """Slugs of all topic dossiers."""
        tdir = self._store.topics_dir()
        if not os.path.isdir(tdir):
            return []
        return sorted(n for n in os.listdir(tdir) if not n.startswith("."))

    # --- refresh (keep info current as sources change / Q&A accrues) -------
    def pending_sources(self) -> list[str]:
        """Raw sources new, changed, or not yet distilled into facts."""
        return _pending_sources(self)

    def pending_qa(self) -> list[QAEntry]:
        """Q&A entries not yet distilled into facts."""
        return _pending_qa(self)

    def needs_refresh(self) -> bool:
        """True when uningested source/Q&A material exists (refresh warranted)."""
        return _needs_refresh(self)

    def refresh(
        self, mode: str = "soft", *, ingest_fn=None, apply: bool = True
    ) -> RefreshReport:
        """Refresh ``info`` from changed sources + undistilled Q&A.

        ``ingest_fn(item)`` supplies extraction (intelligence is external); with
        ``apply=False`` the result is a non-destructive preview. See
        :mod:`hired.candidate.refresh`.
        """
        return _refresh(self, mode, ingest_fn=ingest_fn, apply=apply)

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
        # Topics index: point to where deeper, free-form detail lives.
        topic_names = self.topics()
        if topic_names:
            lines.append("## topics")
            for name in topic_names:
                dossier = TopicDossier(self._store.topic_dir(name), name=name)
                overview = dossier.overview
                headline = (
                    overview.splitlines()[0].lstrip("# ").strip() if overview else name
                )
                lines.append(f"- **{name}** — {headline}  (`info/topics/{name}/`)")
            lines.append("")
        text = "\n".join(lines).rstrip() + "\n"
        self._store.write_synopsis(text)
        return text

    @property
    def synopsis(self) -> str:
        """The last persisted synopsis, regenerating it if absent."""
        text = self._store.read_synopsis()
        return text if text is not None else self.regenerate_synopsis()
