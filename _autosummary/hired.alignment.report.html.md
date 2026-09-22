# hired.alignment.report

Render an [`AlignmentReport`](hired.alignment.base.html.md#hired.alignment.base.AlignmentReport) to Markdown.

Verdict-first (BLUF), evidence-quoted, banded — deliberately *not* a single
false-precision percentage. The four buckets are grouped so the reader sees, in
order: what’s strong, what transfers, what’s learnable (with the AI-leverage
note), what’s genuinely hard, and what we still need to ask.

See `misc/docs/DESIGN.md` §6, and the research in
`misc/docs/research/jd-candidate-matching.md`.

### Functions

| [`render_report_markdown`](#hired.alignment.report.render_report_markdown)(report)   | Render the report as a Markdown string.   |
|-----------------------------------------------------------------------------------|-------------------------------------------|

### hired.alignment.report.render_report_markdown(report)

Render the report as a Markdown string.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)
