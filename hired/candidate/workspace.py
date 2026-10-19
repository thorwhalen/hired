"""The per-engagement facade: alignment reports, company research, interview prep.

A :class:`JDWorkspace` is the domain entry point for work on **one engagement** —
one *or a group of* related job descriptions of the same company. It wraps a
:class:`~hired.persistence.base.JDStore` with validated, intention-revealing
methods and a back-reference to the owning
:class:`~hired.candidate.knowledge_base.CandidateKnowledgeBase` (so an alignment
agent has both the candidate's knowledge and the engagement's work products at hand).

Obtain one via ``kb.jd(jd_id, company=..., label=...)`` — never construct directly.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from hired.candidate.base import _utcnow, slug
from hired.persistence.base import JDStore, validate_name

if TYPE_CHECKING:
    from hired.alignment.base import AlignmentReport
    from hired.candidate.knowledge_base import CandidateKnowledgeBase


class JDWorkspace:
    """Reports, company research, interview-prep briefings, and parsed jobs for one engagement.

    >>> import tempfile, os
    >>> os.environ['HIRED_DATA_DIR'] = tempfile.mkdtemp()
    >>> from hired.candidate import CandidateKnowledgeBase
    >>> kb = CandidateKnowledgeBase()
    >>> ws = kb.jd('acme', company='Acme, Inc.', label='Acme roles')
    >>> ws.save_report('staff-ds', {'verdict': {'recommendation': 'apply'}})
    >>> ws.get_report('staff-ds')['verdict']['recommendation']
    'apply'
    >>> ws.meta['company']
    'Acme, Inc.'
    """

    def __init__(
        self, kb: CandidateKnowledgeBase, jd_id: str, *, store: JDStore | None = None
    ) -> None:
        self.kb: CandidateKnowledgeBase = kb
        self.jd_id: str = jd_id
        self.store: JDStore = store or JDStore(kb.user, jd_id, root=kb._store._root)

    # --- engagement meta ---------------------------------------------------
    @property
    def meta(self) -> dict[str, Any]:
        return self.store.read_meta()

    def set_meta(self, **fields: Any) -> None:
        meta = self.store.read_meta()
        meta.update({k: v for k, v in fields.items() if v is not None})
        self.store.write_meta(meta)

    # --- jobs (parsed JDs) -------------------------------------------------
    def save_job(self, job_id: str, data: dict[str, Any]) -> None:
        self.store.jobs[job_id] = data

    def get_job(self, job_id: str) -> dict[str, Any]:
        return self.store.jobs[job_id]

    def jobs(self) -> list[str]:
        return list(self.store.jobs)

    # --- alignment reports (keyed by job id; archives prior versions) ------
    def save_report(
        self, job_id: str, data: dict[str, Any], *, archive: bool = True
    ) -> None:
        """Persist the current alignment report, archiving the prior one first.

        Archiving (on by default) snapshots any existing report into
        ``report_history`` so the alignment-review agent can diff versions. The
        snapshot is keyed by the *archived* report's ``created_at`` (else now),
        made filename-safe, and never overwrites an earlier snapshot.
        """
        validate_name(job_id, kind="job id")  # a key, never a path
        if archive and job_id in self.store.reports:
            prior = self.store.reports[job_id]
            self.store.report_history[self._history_key(job_id, prior)] = prior
        self.store.reports[job_id] = data

    def _history_key(self, job_id: str, report: dict[str, Any]) -> str:
        # ':' is invalid in Windows filenames and '/' would nest: keep [A-Za-z0-9._-]
        stamp = re.sub(r"[^A-Za-z0-9._-]", "-", report.get("created_at") or _utcnow())
        key, n = f"{job_id}/{stamp}", 1
        while key in self.store.report_history:
            n += 1
            key = f"{job_id}/{stamp}-{n}"
        return key

    def save_alignment(
        self, draft: "AlignmentReport | dict[str, Any]", *, job_id: str | None = None
    ) -> "AlignmentReport":
        """Finalize an analyst-drafted alignment report and save it; return it.

        Whatever produced the draft — the ``hired-align`` skill, the ``hired
        analyze`` command, or an injected-LLM analyzer — this is the one path from
        a draft to a persisted report: :func:`~hired.alignment.finalize_report`
        re-derives everything deterministic, then :meth:`save_report` archives the
        previous version. ``job_id`` overrides the draft's own.
        """
        from hired.alignment import finalize_report

        final = finalize_report(draft)
        if job_id:
            final.job_id = job_id
        validate_name(final.job_id, kind="job id")
        if not final.company:
            final.company = self.meta.get("company") or ""
        self.save_report(final.job_id, final.model_dump(mode="json"))
        return final

    def get_report(self, job_id: str) -> dict[str, Any]:
        return self.store.reports[job_id]

    def reports(self) -> list[str]:
        return list(self.store.reports)

    def report_versions(self, job_id: str) -> list[str]:
        """Keys of archived prior versions of a job's report (chronological)."""
        prefix = f"{job_id}/"
        return sorted(k for k in self.store.report_history if k.startswith(prefix))

    # --- company research --------------------------------------------------
    def save_company_report(self, company: str, data: dict[str, Any]) -> None:
        """Persist a company/people research report (keyed by company name)."""
        self.store.company[slug(company)] = data

    def get_company_report(self, company: str) -> dict[str, Any]:
        return self.store.company[slug(company)]

    def companies(self) -> list[str]:
        return list(self.store.company)

    # --- interview-prep briefings -----------------------------------------
    def save_briefing(self, key: str, data: dict[str, Any]) -> None:
        """Persist an interview-prep research briefing (keyed by subject/job)."""
        self.store.interview_prep[slug(key)] = data

    def get_briefing(self, key: str) -> dict[str, Any]:
        return self.store.interview_prep[slug(key)]

    def briefings(self) -> list[str]:
        return list(self.store.interview_prep)
