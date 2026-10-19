"""Render an :class:`~hired.alignment.base.AlignmentReport` to Markdown or HTML.

Verdict-first (BLUF), evidence-quoted, banded — deliberately *not* a single
false-precision percentage. The four buckets are grouped so the reader sees, in
order: what's strong, what transfers, what's learnable (with the AI-leverage
note), what's genuinely hard, and what we still need to ask.

Formats are a strategy registry (:data:`REPORT_RENDERERS`, dispatched by
:func:`render_report`): add one by registering a ``report -> str`` function. The
HTML renderer is a single self-contained page (inline CSS, light/dark aware, no
external assets), suitable for opening in a browser or publishing as-is.

See ``misc/docs/DESIGN.md`` §6, and the research in
``misc/docs/research/jd-candidate-matching.md``.
"""

from __future__ import annotations

from collections.abc import Callable
from html import escape
from typing import Any

from hired.alignment.base import AlignmentReport, Bucket, RequirementRecord

_BUCKET_HEADINGS = {
    Bucket.STRONG_MATCH: "✅ Strong match",
    Bucket.ADJACENT_TRANSFERABLE: "🔄 Adjacent / transferable",
    Bucket.GAP_LEARNABLE: "📈 Gap — learnable",
    Bucket.GAP_HARD: "⛔ Gap — hard to learn",
}
_UNKNOWN_HEADING = "❓ Not yet known"
_BUCKET_ORDER = [
    Bucket.STRONG_MATCH,
    Bucket.ADJACENT_TRANSFERABLE,
    Bucket.GAP_LEARNABLE,
    Bucket.GAP_HARD,
]


def _group_by_bucket(
    report: AlignmentReport,
) -> tuple[dict[Bucket, list[RequirementRecord]], list[RequirementRecord]]:
    """Records per bucket (in display order) and the unresolved (unknown) ones."""
    by_bucket: dict[Bucket, list[RequirementRecord]] = {b: [] for b in _BUCKET_ORDER}
    unknowns: list[RequirementRecord] = []
    for rec in report.requirements:
        if rec.bucket is None:
            unknowns.append(rec)
        else:
            by_bucket[rec.bucket].append(rec)
    return by_bucket, unknowns


def _close_bits(rec: RequirementRecord) -> list[str]:
    """Closeability annotations for a gap record (empty for non-gaps)."""
    if rec.bucket not in (Bucket.GAP_LEARNABLE, Bucket.GAP_HARD):
        return []
    bits = []
    if rec.closeability:
        bits.append(rec.closeability.value)
    if rec.time_to_close:
        bits.append(f"~{rec.time_to_close.value}")
    if rec.ai_leverage.value != "none":
        bits.append(f"AI-leverage: {rec.ai_leverage.value}")
    return bits


def _title(report: AlignmentReport) -> str:
    head = f"Alignment: {report.job_title or report.job_id}"
    return f"{head} — {report.company}" if report.company else head


def _record_line(rec: RequirementRecord) -> str:
    r = rec.requirement
    lvl = f"(need L{r.required_level} · have L{rec.candidate_level})"
    line = f"- **{r.text}** {lvl}"
    if rec.match_type.value == "adjacent" and rec.adjacency_basis:
        line += (
            f"\n  - _transfers from:_ {rec.source_skill or '—'} — {rec.adjacency_basis}"
        )
    bits = _close_bits(rec)
    if bits:
        line += f"\n  - _close:_ {' · '.join(bits)}"
    if rec.evidence and rec.evidence.quote:
        line += f'\n  - _evidence:_ "{rec.evidence.quote}"'
    if rec.talking_point:
        line += f"\n  - _talking point:_ {rec.talking_point}"
    return line


def render_report_markdown(report: AlignmentReport) -> str:
    """Render the report as a Markdown string."""
    v = report.verdict
    out: list[str] = []
    out.append(f"# {_title(report)}")
    out.append("")

    # --- verdict (BLUF) ---------------------------------------------------
    out.append(
        f"**Verdict: {v.recommendation.value.replace('_', ' ').upper()}** "
        f"· confidence: {v.confidence.value} · fit: {report.score_summary.fit_band.value}"
    )
    if v.headline:
        out.append("")
        out.append(v.headline)
    if v.key_reasons:
        out.append("")
        for reason in v.key_reasons[:5]:
            out.append(f"- {reason}")

    # --- bucket counts ----------------------------------------------------
    counts = report.score_summary.bucket_counts
    if counts:
        out.append("")
        summary = " · ".join(
            f"{_BUCKET_HEADINGS[b].split(' ', 1)[1]}: {counts.get(b.value, 0)}"
            for b in _BUCKET_ORDER
        )
        unknown = sum(1 for r in report.requirements if r.bucket is None)
        out.append(f"_Requirements — {summary} · ❓ needs clarification: {unknown}_")

    # --- blocking gaps (surface even when verdict=apply) ------------------
    if report.blocking_gaps:
        out.append("")
        out.append("## ⛔ Blocking gaps")
        for rec in report.blocking_gaps:
            out.append(_record_line(rec))

    # --- per-bucket breakdown --------------------------------------------
    by_bucket, unknowns = _group_by_bucket(report)
    sections = [(_BUCKET_HEADINGS[b], by_bucket[b]) for b in _BUCKET_ORDER]
    for heading, recs in [*sections, (_UNKNOWN_HEADING, unknowns)]:
        if not recs:
            continue
        out.append("")
        out.append(f"## {heading}")
        for rec in recs:
            out.append(_record_line(rec))

    # --- clarifications (the questions to ask) ----------------------------
    if report.clarifications:
        out.append("")
        out.append("## ❓ Questions to clarify (highest-value first)")
        for c in report.clarifications:
            q = c.question or "(question to be drafted)"
            out.append(f"- {q}")
            if c.reason:
                out.append(f"  - _why:_ {c.reason} (info-gain {c.info_gain})")

    # --- next actions -----------------------------------------------------
    if report.next_actions:
        out.append("")
        out.append("## Next actions")
        for a in sorted(report.next_actions, key=lambda x: x.priority)[:3]:
            line = f"{a.priority}. {a.action}"
            if a.expected_effect:
                line += f" — {a.expected_effect}"
            out.append(line)

    # --- interview prep ---------------------------------------------------
    ip = report.interview_prep
    if ip.summary or ip.talking_points or ip.proactive_disclosure:
        out.append("")
        out.append("## Interview prep")
        if ip.summary:
            out.append(ip.summary)
        for tp in ip.talking_points:
            out.append(f"- {tp}")
        if ip.proactive_disclosure:
            out.append("")
            out.append(f"_Proactive disclosure:_ {ip.proactive_disclosure}")

    return "\n".join(out).rstrip() + "\n"


# --------------------------------------------------------------------------- #
# HTML
# --------------------------------------------------------------------------- #
_BUCKET_CSS_CLASS = {
    Bucket.STRONG_MATCH: "strong",
    Bucket.ADJACENT_TRANSFERABLE: "adjacent",
    Bucket.GAP_LEARNABLE: "learnable",
    Bucket.GAP_HARD: "hard",
}

_HTML_CSS = """
:root { --bg:#fbfbfa; --fg:#1d1d1f; --muted:#6b6b70; --card:#ffffff; --line:#e3e3e0;
  --strong:#1f7a4d; --adjacent:#2f6db3; --learnable:#a86a00; --hard:#b3261e;
  --unknown:#6b6b70; }
@media (prefers-color-scheme: dark) { :root { --bg:#161618; --fg:#ececee;
  --muted:#a0a0a8; --card:#1f1f22; --line:#33333a; --strong:#5cc28f;
  --adjacent:#7fb0ef; --learnable:#e0a83d; --hard:#f07a72; --unknown:#a0a0a8; } }
* { box-sizing:border-box; }
body { margin:0; background:var(--bg); color:var(--fg); line-height:1.5;
  font:16px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
main { max-width:860px; margin:0 auto; padding:24px 16px 64px; }
h1 { font-size:1.6rem; margin:0 0 12px; }
h2 { font-size:1.15rem; margin:32px 0 8px; padding-bottom:4px;
  border-bottom:1px solid var(--line); }
.verdict { background:var(--card); border:1px solid var(--line); border-radius:10px;
  padding:16px; }
.verdict .rec { font-weight:700; font-size:1.2rem; letter-spacing:.02em; }
.meta { color:var(--muted); font-size:.9rem; }
.counts { display:flex; flex-wrap:wrap; gap:8px; margin:12px 0 0; padding:0;
  list-style:none; }
.counts li { border:1px solid var(--line); border-radius:999px; padding:2px 10px;
  font-size:.85rem; background:var(--card); }
ul.records { list-style:none; padding:0; margin:0; }
.record { background:var(--card); border:1px solid var(--line);
  border-left:4px solid var(--unknown); border-radius:8px; padding:10px 12px;
  margin:8px 0; }
.record.strong { border-left-color:var(--strong); }
.record.adjacent { border-left-color:var(--adjacent); }
.record.learnable { border-left-color:var(--learnable); }
.record.hard { border-left-color:var(--hard); }
.record .text { font-weight:600; }
.record .level { color:var(--muted); font-size:.85rem; margin-left:6px; }
.record dl { margin:6px 0 0; display:grid; grid-template-columns:max-content 1fr;
  gap:2px 10px; font-size:.9rem; }
.record dt { color:var(--muted); }
.record dd { margin:0; overflow-wrap:anywhere; }
blockquote { margin:0; font-style:italic; }
ol, ul.plain { padding-left:20px; }
"""


def _html_record(rec: RequirementRecord) -> str:
    r = rec.requirement
    css = _BUCKET_CSS_CLASS.get(rec.bucket, "unknown") if rec.bucket else "unknown"
    details: list[tuple[str, str]] = []
    if rec.match_type.value == "adjacent" and rec.adjacency_basis:
        details.append(
            (
                "transfers from",
                f"{escape(rec.source_skill or '—')} — {escape(rec.adjacency_basis)}",
            )
        )
    bits = _close_bits(rec)
    if bits:
        details.append(("close", escape(" · ".join(bits))))
    if rec.uncertainty_reason and rec.bucket is None:
        details.append(("unknown because", escape(rec.uncertainty_reason)))
    if rec.evidence and rec.evidence.quote:
        details.append(
            ("evidence", f"<blockquote>“{escape(rec.evidence.quote)}”</blockquote>")
        )
    if rec.talking_point:
        details.append(("talking point", escape(rec.talking_point)))
    dl = (
        "<dl>" + "".join(f"<dt>{k}</dt><dd>{v}</dd>" for k, v in details) + "</dl>"
        if details
        else ""
    )
    level = f"need L{r.required_level} · have L{rec.candidate_level}"
    return (
        f'<li class="record {css}"><span class="text">{escape(r.text)}</span>'
        f'<span class="level">({level})</span>{dl}</li>'
    )


def _html_records(heading: str, records: list[RequirementRecord]) -> list[str]:
    if not records:
        return []
    items = "".join(_html_record(rec) for rec in records)
    return [f"<h2>{escape(heading)}</h2>", f'<ul class="records">{items}</ul>']


def render_report_html(report: AlignmentReport) -> str:
    """Render the report as a self-contained HTML page (inline CSS, no assets).

    >>> from hired.alignment import AlignmentReport, Verdict, Recommendation
    >>> page = render_report_html(AlignmentReport(job_id='ds', company='Acme <Inc>',
    ...     verdict=Verdict(recommendation=Recommendation.APPLY, headline='Go')))
    >>> page.startswith('<!doctype html>'), 'Acme &lt;Inc&gt;' in page
    (True, True)
    """
    v = report.verdict
    title = escape(_title(report))
    body: list[str] = [f"<h1>{title}</h1>"]

    # --- verdict (BLUF) ---------------------------------------------------
    verdict = [
        f'<div class="rec">Verdict: '
        f"{escape(v.recommendation.value.replace('_', ' ').upper())}</div>",
        f'<div class="meta">confidence: {escape(v.confidence.value)} · '
        f"fit: {escape(report.score_summary.fit_band.value)}"
        + (f" · {escape(report.created_at)}" if report.created_at else "")
        + "</div>",
    ]
    if v.headline:
        verdict.append(f"<p>{escape(v.headline)}</p>")
    if v.key_reasons:
        verdict.append(
            '<ul class="plain">'
            + "".join(f"<li>{escape(x)}</li>" for x in v.key_reasons[:5])
            + "</ul>"
        )
    by_bucket, unknowns = _group_by_bucket(report)
    counts = report.score_summary.bucket_counts
    if counts or report.requirements:
        chips = [
            f"<li>{escape(_BUCKET_HEADINGS[b])}: "
            f"{counts.get(b.value, len(by_bucket[b]))}</li>"
            for b in _BUCKET_ORDER
        ]
        chips.append(f"<li>❓ needs clarification: {len(unknowns)}</li>")
        verdict.append(f'<ul class="counts">{"".join(chips)}</ul>')
    body.append(f'<section class="verdict">{"".join(verdict)}</section>')

    # --- blocking gaps, buckets, unknowns ---------------------------------
    body += _html_records("⛔ Blocking gaps", report.blocking_gaps)
    for bucket in _BUCKET_ORDER:
        body += _html_records(_BUCKET_HEADINGS[bucket], by_bucket[bucket])
    body += _html_records(_UNKNOWN_HEADING, unknowns)

    # --- clarifications ---------------------------------------------------
    if report.clarifications:
        items = []
        for c in report.clarifications:
            q = escape(c.question or "(question to be drafted)")
            why = (
                f'<div class="meta">why: {escape(c.reason)} '
                f"(info-gain {c.info_gain})</div>"
                if c.reason
                else ""
            )
            items.append(f"<li>{q}{why}</li>")
        body.append("<h2>❓ Questions to clarify (highest-value first)</h2>")
        body.append(f"<ol>{''.join(items)}</ol>")

    # --- next actions -----------------------------------------------------
    if report.next_actions:
        items = []
        for a in sorted(report.next_actions, key=lambda x: x.priority)[:3]:
            effect = f" — {escape(a.expected_effect)}" if a.expected_effect else ""
            items.append(f"<li>{escape(a.action)}{effect}</li>")
        body.append("<h2>Next actions</h2>")
        body.append(f"<ol>{''.join(items)}</ol>")

    # --- interview prep ---------------------------------------------------
    ip = report.interview_prep
    if ip.summary or ip.talking_points or ip.proactive_disclosure:
        body.append("<h2>Interview prep</h2>")
        if ip.summary:
            body.append(f"<p>{escape(ip.summary)}</p>")
        if ip.talking_points:
            body.append(
                '<ul class="plain">'
                + "".join(f"<li>{escape(t)}</li>" for t in ip.talking_points)
                + "</ul>"
            )
        if ip.proactive_disclosure:
            body.append(
                f"<p><em>Proactive disclosure:</em> {escape(ip.proactive_disclosure)}</p>"
            )

    return (
        '<!doctype html>\n<html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f"<title>{title}</title><style>{_HTML_CSS}</style></head>"
        f"<body><main>{''.join(body)}</main></body></html>\n"
    )


# --------------------------------------------------------------------------- #
# Format registry (strategy) + dispatcher
# --------------------------------------------------------------------------- #
#: ``format name -> renderer``. Register a new format by adding an entry.
REPORT_RENDERERS: dict[str, Callable[[AlignmentReport], str]] = {
    "markdown": render_report_markdown,
    "md": render_report_markdown,
    "html": render_report_html,
}


def render_report(
    report: AlignmentReport | dict[str, Any], fmt: str = "markdown"
) -> str:
    """Render ``report`` (a model or its JSON dict) in the named format.

    >>> from hired.alignment import AlignmentReport, Verdict, Recommendation
    >>> r = {'job_id': 'ds', 'verdict': {'recommendation': 'apply'}}
    >>> render_report(r).splitlines()[0]
    '# Alignment: ds'
    >>> render_report(r, 'pdf')
    Traceback (most recent call last):
      ...
    ValueError: Unknown report format 'pdf'; choose from: html, markdown, md
    """
    renderer = REPORT_RENDERERS.get(fmt)
    if renderer is None:
        raise ValueError(
            f"Unknown report format {fmt!r}; choose from: "
            + ", ".join(sorted(REPORT_RENDERERS))
        )
    return renderer(AlignmentReport.model_validate(report))
