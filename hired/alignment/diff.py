"""Deterministic diff between two alignment reports.

Used by the alignment-review workflow (heavy mode) to surface *what changed*
between an existing report and a freshly regenerated one — so the change set is
auditable and reviewable before anything is applied. Requirements are matched by
their verbatim text (stable across regenerations); the diff reports bucket moves,
verdict changes, and added/removed requirements and clarifications.

See ``misc/docs/DESIGN.md`` §6 and the alignment-review agent.
"""

from __future__ import annotations

from typing import Any


def _req_index(report: dict) -> dict[str, dict]:
    """Map requirement text -> its record, for matching across versions."""
    out: dict[str, dict] = {}
    for rec in report.get("requirements", []):
        text = (rec.get("requirement") or {}).get("text", "")
        if text:
            out[text] = rec
    return out


def _bucket(rec: dict | None) -> str:
    if rec is None:
        return "absent"
    return rec.get("bucket") or "needs_clarification"


def diff_reports(old: dict, new: dict) -> dict[str, Any]:
    """Return a structured diff of two alignment-report dicts.

    Both inputs are ``AlignmentReport.model_dump()`` dicts. The result has:

    - ``verdict_changed`` / ``verdict_old`` / ``verdict_new``
    - ``fit_old`` / ``fit_new``
    - ``bucket_changes``: list of ``{requirement, from, to}`` for requirements
      whose bucket moved (the heart of a refresh — typically UNKNOWN→known as
      Q&A resolves false negatives)
    - ``added`` / ``removed``: requirement texts present in only one version
    - ``clarifications_resolved``: clarifying questions in old but not new
    """
    oi, ni = _req_index(old), _req_index(new)
    bucket_changes = []
    for text in oi.keys() & ni.keys():
        ob, nb = _bucket(oi[text]), _bucket(ni[text])
        if ob != nb:
            bucket_changes.append({"requirement": text, "from": ob, "to": nb})

    ov = old.get("verdict") or {}
    nv = new.get("verdict") or {}
    old_clar = {
        c.get("question", "")
        for c in old.get("clarifications", [])
        if c.get("question")
    }
    new_clar = {
        c.get("question", "")
        for c in new.get("clarifications", [])
        if c.get("question")
    }

    return {
        "verdict_changed": ov.get("recommendation") != nv.get("recommendation"),
        "verdict_old": ov.get("recommendation"),
        "verdict_new": nv.get("recommendation"),
        "fit_old": (old.get("score_summary") or {}).get("fit_band"),
        "fit_new": (new.get("score_summary") or {}).get("fit_band"),
        "bucket_changes": sorted(bucket_changes, key=lambda d: d["requirement"]),
        "added": sorted(ni.keys() - oi.keys()),
        "removed": sorted(oi.keys() - ni.keys()),
        "clarifications_resolved": sorted(old_clar - new_clar),
        "n_changes": len(bucket_changes)
        + int(ov.get("recommendation") != nv.get("recommendation"))
        + len(ni.keys() ^ oi.keys()),
    }


def summarize_diff(diff: dict) -> str:
    """A short human-readable summary of :func:`diff_reports` output."""
    lines = []
    if diff["verdict_changed"]:
        lines.append(f"Verdict: {diff['verdict_old']} → {diff['verdict_new']}")
    if diff["fit_old"] != diff["fit_new"]:
        lines.append(f"Fit band: {diff['fit_old']} → {diff['fit_new']}")
    for ch in diff["bucket_changes"]:
        lines.append(f"• {ch['from']} → {ch['to']}: {ch['requirement']}")
    for t in diff["added"]:
        lines.append(f"+ new requirement: {t}")
    for t in diff["removed"]:
        lines.append(f"- dropped requirement: {t}")
    for q in diff["clarifications_resolved"]:
        lines.append(f"✓ resolved question: {q}")
    return "\n".join(lines) if lines else "No material changes."
