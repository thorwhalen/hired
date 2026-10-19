# hired.cli

Command-line operations for the candidate-knowledge + JD-alignment workflow.

Each function here is a plain, importable operation — no CLI library is imported —
and [`CLI_FUNCS`](#hired.cli.CLI_FUNCS) is the single source of truth for what the `hired` command
exposes (see `hired.__main__`, which projects it onto a parser with `cw`).

Every operation takes a keyword-only `user` (`--user` on the command line),
resolved by [`hired.persistence.resolve_user()`](hired.persistence.html.md#hired.persistence.resolve_user): the given name, else
`$HIRED_USER`, else `"me"`. So a single-candidate setup needs no flag at all,
and several candidates coexist under `users/<user>/`.

The *intelligence* stays outside: `ingest` takes fact records an extractor (the
`hired-profile-ingest` subagent, or an LLM) already produced, and `analyze`
takes an analyst-drafted report; the commands validate, derive what is
deterministic, and persist.

```pycon
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
```

### Module Attributes

| [`CLI_FUNCS`](#hired.cli.CLI_FUNCS)   | The operations the `hired` command exposes (SSOT for every surface).   |
|--------------------------------------------------------------|------------------------------------------------------------------------|

### Functions

| [`add_source`](#hired.cli.add_source)(path, \*[, name, user])               | Store a raw source document (CV, bio, publication list...) for a candidate.            |
|---------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------|
| [`analyze`](#hired.cli.analyze)(report, jd, \*[, job_id, company, user]) | Finalize an analyst-drafted alignment report (JSON) and save it under engagement `jd`. |
| [`facts`](#hired.cli.facts)(\*[, category, tag, user])                 | List a candidate's current (asserted) fact statements.                                 |
| [`ingest`](#hired.cli.ingest)(records, \*[, source, user])              | Add extracted fact records (a JSON list) to a candidate's knowledge base.              |
| [`jds`](#hired.cli.jds)(\*[, user])                                  | List a candidate's engagements (one per company; 1+ roles each).                       |
| [`report`](#hired.cli.report)(jd[, job_id, fmt, output, user])          | Render a saved alignment report (`--fmt markdown|html`).                               |
| [`reports`](#hired.cli.reports)(jd, \*[, user])                          | List the job ids that have an alignment report in engagement `jd`.                     |
| [`status`](#hired.cli.status)(\*[, user])                               | Summarize a candidate's knowledge base: counts, pending material, engagements.         |
| [`synopsis`](#hired.cli.synopsis)(\*[, regenerate, user])                 | Print a candidate's synopsis (`--regenerate` rebuilds it from the facts).              |
| [`users`](#hired.cli.users)()                                          | List the candidates that have data (one `users/<user>/` directory each).               |

### hired.cli.CLI_FUNCS *= [<function users>, <function status>, <function add_source>, <function ingest>, <function facts>, <function synopsis>, <function jds>, <function analyze>, <function reports>, <function report>]*

The operations the `hired` command exposes (SSOT for every surface).

### hired.cli.add_source(path, , name=None, user=None)

Store a raw source document (CV, bio, publication list…) for a candidate.

Prints the source key. Its facts are added later with `ingest`.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### hired.cli.analyze(report, jd, , job_id=None, company=None, user=None)

Finalize an analyst-drafted alignment report (JSON) and save it under engagement `jd`.

Every requirement is re-classified with the deterministic rubric, bucket
counts, blocking gaps and the ranked clarifying questions are rebuilt, and
the report is saved (the previous version of the same job’s report is
archived). Prints the saved job id and the resulting verdict line.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### hired.cli.facts(, category=None, tag=None, user=None)

List a candidate’s current (asserted) fact statements.

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]

### hired.cli.ingest(records, , source=None, user=None)

Add extracted fact records (a JSON list) to a candidate’s knowledge base.

`records` is a JSON file holding a list of `{"statement", "category",
"tags", "confidence", "quote", "locator", "is_negation"}` dicts. With
`--source` (a raw-source key, or a file path, which is stored first) the
facts cite that source, their quotes are checked against its text, and a
re-ingest of the same source supersedes the facts of the previous one.
Without it, the facts are recorded as externally sourced.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]

### hired.cli.jds(, user=None)

List a candidate’s engagements (one per company; 1+ roles each).

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]

### hired.cli.report(jd, job_id=None, , fmt='markdown', output=None, user=None)

Render a saved alignment report (`--fmt markdown|html`).

`job_id` may be omitted when the engagement has a single report. With
`--output` the rendering is written to that file (and its path printed);
otherwise it is printed.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### hired.cli.reports(jd, , user=None)

List the job ids that have an alignment report in engagement `jd`.

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]

### hired.cli.status(, user=None)

Summarize a candidate’s knowledge base: counts, pending material, engagements.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]

### hired.cli.synopsis(, regenerate=False, user=None)

Print a candidate’s synopsis (`--regenerate` rebuilds it from the facts).

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### hired.cli.users()

List the candidates that have data (one `users/<user>/` directory each).

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]
