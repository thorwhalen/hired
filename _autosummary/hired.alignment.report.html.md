# hired.alignment.report

Render an [`AlignmentReport`](hired.alignment.base.html.md#hired.alignment.base.AlignmentReport) to Markdown or HTML.

Verdict-first (BLUF), evidence-quoted, banded — deliberately *not* a single
false-precision percentage. The four buckets are grouped so the reader sees, in
order: what’s strong, what transfers, what’s learnable (with the AI-leverage
note), what’s genuinely hard, and what we still need to ask.

Formats are a strategy registry ([`REPORT_RENDERERS`](#hired.alignment.report.REPORT_RENDERERS), dispatched by
[`render_report()`](#hired.alignment.report.render_report)): add one by registering a `report -> str` function. The
HTML renderer is a single self-contained page (inline CSS, light/dark aware, no
external assets), suitable for opening in a browser or publishing as-is.

See `misc/docs/DESIGN.md` §6, and the research in
`misc/docs/research/jd-candidate-matching.md`.

### Module Attributes

| [`REPORT_RENDERERS`](#hired.alignment.report.REPORT_RENDERERS)   | `format name -> renderer`.   |
|---------------------------------------------------------------------|------------------------------|

### Functions

| [`render_report`](#hired.alignment.report.render_report)(report[, fmt])   | Render `report` (a model or its JSON dict) in the named format.          |
|---------------------------------------------------------------------------------|--------------------------------------------------------------------------|
| [`render_report_html`](#hired.alignment.report.render_report_html)(report)     | Render the report as a self-contained HTML page (inline CSS, no assets). |
| [`render_report_markdown`](#hired.alignment.report.render_report_markdown)(report) | Render the report as a Markdown string.                                  |

### hired.alignment.report.REPORT_RENDERERS *: [dict](https://docs.python.org/3/builtins/stdtypes.html#dict)[[str](https://docs.python.org/3/builtins/stdtypes.html#str), [Callable](https://docs.python.org/3/library/collections.abc.html#collections.abc.Callable)[[[AlignmentReport](hired.alignment.base.html.md#hired.alignment.base.AlignmentReport)], [str](https://docs.python.org/3/builtins/stdtypes.html#str)]]* *= {'html': <function render_report_html>, 'markdown': <function render_report_markdown>, 'md': <function render_report_markdown>}*

`format name -> renderer`. Register a new format by adding an entry.

### hired.alignment.report.render_report(report, fmt='markdown')

Render `report` (a model or its JSON dict) in the named format.

```pycon
>>> from hired.alignment import AlignmentReport, Verdict, Recommendation
>>> r = {'job_id': 'ds', 'verdict': {'recommendation': 'apply'}}
>>> render_report(r).splitlines()[0]
'# Alignment: ds'
>>> render_report(r, 'pdf')
Traceback (most recent call last):
  ...
ValueError: Unknown report format 'pdf'; choose from: html, markdown, md
```

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### hired.alignment.report.render_report_html(report)

Render the report as a self-contained HTML page (inline CSS, no assets).

```pycon
>>> from hired.alignment import AlignmentReport, Verdict, Recommendation
>>> page = render_report_html(AlignmentReport(job_id='ds', company='Acme <Inc>',
...     verdict=Verdict(recommendation=Recommendation.APPLY, headline='Go')))
>>> page.startswith('<!doctype html>'), 'Acme &lt;Inc&gt;' in page
(True, True)
```

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### hired.alignment.report.render_report_markdown(report)

Render the report as a Markdown string.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)
