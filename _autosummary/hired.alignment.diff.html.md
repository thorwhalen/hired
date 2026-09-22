# hired.alignment.diff

Deterministic diff between two alignment reports.

Used by the alignment-review workflow (heavy mode) to surface *what changed*
between an existing report and a freshly regenerated one — so the change set is
auditable and reviewable before anything is applied. Requirements are matched by
their verbatim text (stable across regenerations); the diff reports bucket moves,
verdict changes, and added/removed requirements and clarifications.

See `misc/docs/DESIGN.md` §6 and the alignment-review agent.

### Functions

| [`diff_reports`](#hired.alignment.diff.diff_reports)(old, new)   | Return a structured diff of two alignment-report dicts.                                                   |
|---------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------|
| [`summarize_diff`](#hired.alignment.diff.summarize_diff)(diff)     | A short human-readable summary of [`diff_reports()`](#hired.alignment.diff.diff_reports) output. |

### hired.alignment.diff.diff_reports(old, new)

Return a structured diff of two alignment-report dicts.

Both inputs are `AlignmentReport.model_dump()` dicts. The result has:

- `verdict_changed` / `verdict_old` / `verdict_new`
- `fit_old` / `fit_new`
- `bucket_changes`: list of `{requirement, from, to}` for requirements
  whose bucket moved (the heart of a refresh — typically UNKNOWN→known as
  Q&A resolves false negatives)
- `added` / `removed`: requirement texts present in only one version
- `clarifications_resolved`: clarifying questions in old but not new

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]

### hired.alignment.diff.summarize_diff(diff)

A short human-readable summary of [`diff_reports()`](#hired.alignment.diff.diff_reports) output.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)
