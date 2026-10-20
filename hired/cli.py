"""Command-line operations for the candidate-knowledge + JD-alignment workflow.

Each function here is a plain, importable operation — no CLI library is imported —
and :data:`CLI_FUNCS` is the single source of truth for what the ``hired`` command
exposes (see :mod:`hired.__main__`, which projects it onto a parser with ``cw``).

Every operation takes a keyword-only ``user`` (``--user`` on the command line),
resolved by :func:`hired.persistence.resolve_user`: the given name, else
``$HIRED_USER``, else ``"me"``. So a single-candidate setup needs no flag at all,
and several candidates coexist under ``users/<user>/``.

The *intelligence* stays outside: ``ingest`` takes fact records an extractor (the
``hired-profile-ingest`` subagent, or an LLM) already produced, and ``analyze``
takes an analyst-drafted report; the commands validate, derive what is
deterministic, and persist. ``align`` is the one exception: it runs the
injected-LLM analyzer (:mod:`hired.alignment.analyzer`) on raw JD text.

>>> import os, json, tempfile
>>> os.environ['HIRED_DATA_DIR'] = tempfile.mkdtemp()
>>> work = tempfile.mkdtemp()
>>> cv = os.path.join(work, 'cv.md')
>>> _ = open(cv, 'w').write('I built ML pipelines in Python.')
>>> recs = os.path.join(work, 'facts.json')
>>> _ = open(recs, 'w').write(json.dumps([{'statement': 'Builds ML pipelines',
...     'category': 'skill', 'quote': 'built ML pipelines'}]))
>>> ingest(recs, source=cv, user='alice')['added']
1
>>> users()
['alice']
>>> facts(user='alice')
['Builds ML pipelines']
"""

from __future__ import annotations

import json
import os
from typing import Any

from hired.persistence.base import list_users


def _kb(user: str | None, *, must_exist: bool = False):
    """The candidate's knowledge base; ``must_exist`` guards read-only commands.

    Opening a knowledge base creates the candidate's directories, so a read-only
    command with a mistyped ``--user`` would otherwise silently create a new
    (empty) candidate.
    """
    from hired.candidate import CandidateKnowledgeBase
    from hired.persistence import resolve_user

    name = resolve_user(user)
    if must_exist and name not in list_users():
        raise ValueError(
            f"No candidate {name!r}; known: {', '.join(list_users()) or 'none'}"
        )
    return CandidateKnowledgeBase(name)


def _workspace(jd: str, user: str | None):
    """An *existing* engagement's workspace (read-only commands never create one)."""
    kb = _kb(user, must_exist=True)
    if jd not in kb.jds():
        raise ValueError(
            f"No engagement {jd!r} for {kb.user!r}; known: {', '.join(kb.jds()) or 'none'}"
        )
    return kb.jd(jd)


def _read_json(path: str) -> Any:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# --------------------------------------------------------------------------- #
# Candidates
# --------------------------------------------------------------------------- #
def users() -> list[str]:
    """List the candidates that have data (one ``users/<user>/`` directory each)."""
    return list_users()


def status(*, user: str | None = None) -> dict[str, Any]:
    """Summarize a candidate's knowledge base: counts, pending material, engagements."""
    kb = _kb(user, must_exist=True)
    return {
        "user": kb.user,
        "facts": sum(1 for _ in kb.facts()),
        "qa": sum(1 for _ in kb.qa_entries()),
        "sources": kb.sources(),
        "pending_sources": kb.pending_sources(),
        "pending_qa": len(kb.pending_qa()),
        "needs_refresh": kb.needs_refresh(),
        "topics": kb.topics(),
        "jds": kb.jds(),
    }


# --------------------------------------------------------------------------- #
# Ingest
# --------------------------------------------------------------------------- #
def add_source(path: str, *, name: str | None = None, user: str | None = None) -> str:
    """Store a raw source document (CV, bio, publication list...) for a candidate.

    Prints the source key. Its facts are added later with ``ingest``.
    """
    return _kb(user).add_source(path, name=name)


def ingest(
    records: str, *, source: str | None = None, user: str | None = None
) -> dict[str, Any]:
    """Add extracted fact records (a JSON list) to a candidate's knowledge base.

    ``records`` is a JSON file holding a list of ``{"statement", "category",
    "tags", "confidence", "quote", "locator", "is_negation"}`` dicts. With
    ``--source`` (a raw-source key, or a file path, which is stored first) the
    facts cite that source, their quotes are checked against its text, and a
    re-ingest of the same source supersedes the facts of the previous one.
    Without it, the facts are recorded as externally sourced.
    """
    from hired.candidate import SourceKind, ingest_facts

    kb = _kb(user)
    recs = _read_json(records)
    if not isinstance(recs, list):
        raise ValueError(f"{records}: expected a JSON list of fact records")
    if source is None:
        added = ingest_facts(kb, recs, source_kind=SourceKind.EXTERNAL)
        superseded: list[str] = []
        kb.regenerate_synopsis()
    else:
        if os.path.isfile(source):
            source = kb.add_source(source)
        elif source not in kb.sources():
            raise ValueError(
                f"Unknown source {source!r}: not a file, nor one of {kb.sources()}"
            )
        added, superseded = kb.ingest_source(source, recs)
    return {
        "user": kb.user,
        "source": source,
        "added": len(added),
        "superseded": len(superseded),
    }


def facts(
    *, category: str | None = None, tag: str | None = None, user: str | None = None
) -> list[str]:
    """List a candidate's current (asserted) fact statements."""
    from hired.candidate import FactCategory

    cat = FactCategory(category) if category else None
    return [
        ("NOT: " if f.is_negation else "") + f.statement
        for f in _kb(user, must_exist=True).facts(
            category=cat, tags=[tag] if tag else None
        )
    ]


def synopsis(*, regenerate: bool = False, user: str | None = None) -> str:
    """Print a candidate's synopsis (``--regenerate`` rebuilds it from the facts)."""
    kb = _kb(user, must_exist=True)
    return kb.regenerate_synopsis() if regenerate else kb.synopsis


# --------------------------------------------------------------------------- #
# Analyze + report
# --------------------------------------------------------------------------- #
def jds(*, user: str | None = None) -> list[str]:
    """List a candidate's engagements (one per company; 1+ roles each)."""
    return _kb(user, must_exist=True).jds()


def analyze(
    report: str,
    jd: str,
    *,
    job_id: str | None = None,
    company: str | None = None,
    user: str | None = None,
) -> str:
    """Finalize an analyst-drafted alignment report (JSON) and save it under engagement ``jd``.

    Every requirement is re-classified with the deterministic rubric, bucket
    counts, blocking gaps and the ranked clarifying questions are rebuilt, and
    the report is saved (the previous version of the same job's report is
    archived). Prints the saved job id and the resulting verdict line.
    """
    from hired.alignment import AlignmentReport
    from hired.persistence import validate_name

    draft = AlignmentReport.model_validate(_read_json(report))
    if company and not draft.company:
        draft.company = company
    # Validate every id before anything is written (no orphan engagement).
    validate_name(job_id or draft.job_id, kind="job id")
    ws = _kb(user).jd(jd, company=company or draft.company or None)
    final = ws.save_alignment(draft, job_id=job_id)
    return _verdict_line(jd, final)


def _verdict_line(jd: str, final) -> str:
    counts = ", ".join(
        f"{k}={v}" for k, v in final.score_summary.bucket_counts.items() if v
    )
    unknown = sum(1 for r in final.requirements if r.bucket is None)
    return (
        f"{jd}/{final.job_id}: {final.verdict.recommendation.value}"
        f" ({counts or 'no classified requirements'}; unknown={unknown};"
        f" blocking={len(final.blocking_gaps)})"
    )


def align(
    jd: str,
    *,
    jd_text: str,
    job_id: str | None = None,
    job_title: str = "",
    company: str | None = None,
    model: str | None = None,
    n_samples: int = 1,
    nli: bool = False,
    user: str | None = None,
) -> str:
    """Analyse a raw job description (the file ``jd_text``) with an LLM and save the report.

    The autonomous counterpart of ``analyze``: an LLM (the ``ai`` extra, an
    ``OPENAI_API_KEY``) decomposes the JD and judges each requirement against the
    candidate's facts, every judgment must quote a fact verbatim, and the verdict
    is computed deterministically. The JD text is stored as the job under
    engagement ``jd``. ``job_id`` defaults to the file's name without extension;
    ``--n-samples`` > 1 samples each judgment for calibrated confidence; ``--nli``
    adds an entailment check on every match.
    """
    from pathlib import Path

    from hired.alignment import analyzer as _analyzer
    from hired.candidate.base import slug
    from hired.persistence import validate_name

    job_id = job_id or slug(Path(jd_text).stem)
    validate_name(job_id, kind="job id (pass --job-id)")  # before anything is written
    try:
        text = Path(jd_text).read_text(encoding="utf-8")
    except (OSError, UnicodeError) as e:
        raise ValueError(f"Cannot read the JD text file {jd_text!r}: {e}") from e
    if not text.strip():
        raise ValueError(f"The JD text file {jd_text!r} is empty")
    kb = _kb(user, must_exist=True)  # a mistyped --user must not judge zero facts
    llm = _analyzer.LLMAlignmentAnalyzer(
        **({"model": model} if model else {}), n_samples=n_samples, nli=nli
    )
    # Analyse first: an LLM failure (no ai extra, no key) leaves nothing behind.
    draft = llm.analyze(
        text, kb.facts(), job_id=job_id, job_title=job_title, company=company or ""
    )
    ws = kb.jd(jd, company=company)
    ws.save_job(job_id, {"title": job_title, "text": text})
    final = ws.save_alignment(draft)
    return _verdict_line(jd, final)


def reports(jd: str, *, user: str | None = None) -> list[str]:
    """List the job ids that have an alignment report in engagement ``jd``."""
    return _workspace(jd, user).reports()


def report(
    jd: str,
    job_id: str | None = None,
    *,
    fmt: str = "markdown",
    output: str | None = None,
    user: str | None = None,
) -> str:
    """Render a saved alignment report (``--fmt markdown|html``).

    ``job_id`` may be omitted when the engagement has a single report. With
    ``--output`` the rendering is written to that file (and its path printed);
    otherwise it is printed.
    """
    from hired.alignment import render_report

    ws = _workspace(jd, user)
    if job_id is None:
        available = ws.reports()
        if len(available) != 1:
            raise ValueError(
                f"Engagement {jd!r} has {len(available)} reports "
                f"({', '.join(available) or 'none'}); pass a job_id"
            )
        job_id = available[0]
    elif job_id not in ws.reports():
        raise ValueError(
            f"No report {job_id!r} in engagement {jd!r}; "
            f"known: {', '.join(ws.reports()) or 'none'}"
        )
    text = render_report(ws.get_report(job_id), fmt)
    if output is None:
        return text
    with open(output, "w", encoding="utf-8", newline="") as f:
        f.write(text)
    return output


#: The operations the ``hired`` command exposes (SSOT for every surface).
CLI_FUNCS = [
    users,
    status,
    add_source,
    ingest,
    facts,
    synopsis,
    jds,
    analyze,
    align,
    reports,
    report,
]
