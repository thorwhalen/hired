"""Render an :class:`~hired.alignment.base.AlignmentReport` to Markdown.

Verdict-first (BLUF), evidence-quoted, banded — deliberately *not* a single
false-precision percentage. The four buckets are grouped so the reader sees, in
order: what's strong, what transfers, what's learnable (with the AI-leverage
note), what's genuinely hard, and what we still need to ask.

See ``misc/docs/DESIGN.md`` §6, and the research in
``misc/docs/research/jd-candidate-matching.md``.
"""

from __future__ import annotations

from hired.alignment.base import AlignmentReport, Bucket, RequirementRecord

_BUCKET_HEADINGS = {
    Bucket.STRONG_MATCH: "✅ Strong match",
    Bucket.ADJACENT_TRANSFERABLE: "🔄 Adjacent / transferable",
    Bucket.GAP_LEARNABLE: "📈 Gap — learnable",
    Bucket.GAP_HARD: "⛔ Gap — hard to learn",
}
_BUCKET_ORDER = [
    Bucket.STRONG_MATCH,
    Bucket.ADJACENT_TRANSFERABLE,
    Bucket.GAP_LEARNABLE,
    Bucket.GAP_HARD,
]


def _record_line(rec: RequirementRecord) -> str:
    r = rec.requirement
    lvl = f"(need L{r.required_level} · have L{rec.candidate_level})"
    line = f"- **{r.text}** {lvl}"
    if rec.match_type.value == "adjacent" and rec.adjacency_basis:
        line += (
            f"\n  - _transfers from:_ {rec.source_skill or '—'} — {rec.adjacency_basis}"
        )
    if rec.bucket in (Bucket.GAP_LEARNABLE, Bucket.GAP_HARD):
        bits = []
        if rec.closeability:
            bits.append(rec.closeability.value)
        if rec.time_to_close:
            bits.append(f"~{rec.time_to_close.value}")
        if rec.ai_leverage.value != "none":
            bits.append(f"AI-leverage: {rec.ai_leverage.value}")
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
    title = report.job_title or report.job_id
    head = f"# Alignment: {title}"
    if report.company:
        head += f" — {report.company}"
    out.append(head)
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
    by_bucket: dict[Bucket, list[RequirementRecord]] = {b: [] for b in _BUCKET_ORDER}
    unknowns: list[RequirementRecord] = []
    for rec in report.requirements:
        if rec.bucket is None:
            unknowns.append(rec)
        else:
            by_bucket[rec.bucket].append(rec)

    for bucket in _BUCKET_ORDER:
        recs = by_bucket[bucket]
        if not recs:
            continue
        out.append("")
        out.append(f"## {_BUCKET_HEADINGS[bucket]}")
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
