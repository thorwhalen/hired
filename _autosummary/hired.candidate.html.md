# hired.candidate

Candidate knowledge domain: accumulate open-world facts about a candidate.

The public facade is [`CandidateKnowledgeBase`](#hired.candidate.CandidateKnowledgeBase). Schemas ([`Fact`](#hired.candidate.Fact),
[`QAEntry`](#hired.candidate.QAEntry), [`Provenance`](#hired.candidate.Provenance), and the enums) live in
[`hired.candidate.base`](hired.candidate.base.html.md#module-hired.candidate.base); document/Q&A ingest in [`hired.candidate.ingest`](hired.candidate.ingest.html.md#module-hired.candidate.ingest).

See `misc/docs/DESIGN.md` §5.

### Functions

| [`needs_refresh`](#hired.candidate.needs_refresh)(kb)                                 | True when there is uningested source/Q&A material — a refresh is warranted.                           |
|----------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------|
| [`refresh`](#hired.candidate.refresh)(kb[, mode, ingest_fn, apply])             | Refresh `info` from changed sources + undistilled Q&A.                                                |
| [`slug`](#hired.candidate.slug)(text)                                        | A filesystem-safe, extension-less key from an arbitrary label.                                        |
| [`ingest_facts`](#hired.candidate.ingest_facts)(kb, records, \*, source_kind[, ...]) | Validate, quote-check, and persist fact records; return persisted ids.                                |
| [`fact_from_record`](#hired.candidate.fact_from_record)(record, \*, source_kind[, ...])  | Build a (not-yet-persisted) [`Fact`](#hired.candidate.Fact) from a record dict. |
| [`verify_quote`](#hired.candidate.verify_quote)(quote, source_text)                  | True if `quote` is a verbatim substring of `source_text`.                                             |

### Classes

| [`CandidateKnowledgeBase`](#hired.candidate.CandidateKnowledgeBase)([user, store])        | Accumulated, open-world knowledge about a single candidate (user-level).                 |
|-----------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------|
| [`JDWorkspace`](#hired.candidate.JDWorkspace)(kb, jd_id, \*[, store])          | Reports, company research, interview-prep briefings, and parsed jobs for one engagement. |
| [`TopicDossier`](#hired.candidate.TopicDossier)(base_dir, \*[, name])           | One subject's dossier: an `overview.md` plus optional attached files.                    |
| [`RefreshState`](#hired.candidate.RefreshState)(\*\*data)                       | The candidate-info refresh ledger (persisted to `user/info/state.json`).                 |
| [`SourceDigest`](#hired.candidate.SourceDigest)(\*\*data)                       | What we know about one raw source for change detection + provenance.                     |
| [`RefreshItem`](#hired.candidate.RefreshItem)(kind, key, content)              | One unit of pending work for a refresh: a changed source or an undistilled Q&A.          |
| [`RefreshProposal`](#hired.candidate.RefreshProposal)(kind, key, records)          | Proposed fact records for one item (returned when `apply=False`).                        |
| [`RefreshReport`](#hired.candidate.RefreshReport)(mode, applied[, pending, ...]) | Outcome (or preview) of a refresh.                                                       |
| [`Fact`](#hired.candidate.Fact)(\*\*data)                               | One atomic claim about a candidate.                                                      |
| [`QAEntry`](#hired.candidate.QAEntry)(\*\*data)                            | One clarifying question asked of the candidate and their answer.                         |
| [`Provenance`](#hired.candidate.Provenance)(\*\*data)                         | Where a fact came from, with an optional verbatim supporting quote.                      |
| [`FactCategory`](#hired.candidate.FactCategory)(\*values)                       | Coarse category for retrieval and synopsis grouping.                                     |
| [`FactStatus`](#hired.candidate.FactStatus)(\*values)                         | Whether a fact is current or has been superseded by a newer one.                         |
| [`SourceKind`](#hired.candidate.SourceKind)(\*values)                         | Where a piece of provenance came from.                                                   |
| [`ConfidenceLevel`](#hired.candidate.ConfidenceLevel)(\*values)                    | Calibrated confidence in a claim (qualitative, not a raw probability).                   |
| [`MatchState`](#hired.candidate.MatchState)(\*values)                         | Three-valued epistemic state — the core of the honesty contract.                         |

### *class* hired.candidate.CandidateKnowledgeBase(user='me', , store=None)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Accumulated, open-world knowledge about a single candidate (user-level).

```pycon
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
```

#### add_fact(fact)

Persist a fact, returning its id.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

#### add_note(subject, text=None, , files=None)

Record volunteered info about a subject into its dossier.

`text` is appended to the dossier’s `overview.md`; `files` (a
`{name: bytes}` mapping) are attached as detail/media. Returns the
dossier. This is the “by the way, I also did X” entry point — a single
sentence or a whole folder both land here.

* **Return type:**
  [`TopicDossier`](hired.candidate.topics.html.md#hired.candidate.topics.TopicDossier)

#### add_source(src, , name=None)

Store a raw source (file path or bytes) and record its content digest.

Returns the source key (its name in the raw store). The digest (in
`state.json`) lets a later refresh detect new/changed sources without
re-reading everything. Facts extracted from a source cite it by this key.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

#### facts(, category=None, tags=None, status=FactStatus.ASSERTED, include_negations=True)

Iterate facts, optionally filtered by category/tags/status.

By default only `ASSERTED` facts are returned (superseded ones are
hidden). `tags` matches facts containing *any* of the given tags.

* **Return type:**
  [`Iterator`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Iterator)[[`Fact`](hired.candidate.base.html.md#hired.candidate.base.Fact)]

#### jd(jd_id, , company=None, label=None)

Get-or-create the workspace for an engagement (1+ JDs of one company).

`company` / `label` are recorded in the engagement’s `meta` when given.

* **Return type:**
  [`JDWorkspace`](hired.candidate.workspace.html.md#hired.candidate.workspace.JDWorkspace)

#### jds()

Ids of all engagements for this candidate.

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]

#### needs_refresh()

True when uningested source/Q&A material exists (refresh warranted).

* **Return type:**
  [`bool`](https://docs.python.org/3/builtins/functions.html#bool)

#### pending_qa()

Q&A entries not yet distilled into facts.

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`QAEntry`](hired.candidate.base.html.md#hired.candidate.base.QAEntry)]

#### pending_sources()

Raw sources new, changed, or not yet distilled into facts.

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]

#### record_qa(entry, , derived_facts=None)

Append a clarifying Q&A exchange; optionally distill it into facts.

When `derived_facts` (atomic fact records extracted from the answer) are
given, they are ingested with `SourceKind.QA` provenance (`source_id`
= the Q&A id, quotes verified against the answer) and back-linked via the
entry’s `derived_fact_ids` — so a Q&A answer becomes reusable,
discoverable knowledge rather than being buried in the history.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

#### refresh(mode='soft', , ingest_fn=None, apply=True)

Refresh `info` from changed sources + undistilled Q&A.

`ingest_fn(item)` supplies extraction (intelligence is external); with
`apply=False` the result is a non-destructive preview. See
[`hired.candidate.refresh`](#hired.candidate.refresh).

* **Return type:**
  [`RefreshReport`](#hired.candidate.RefreshReport)

#### regenerate_synopsis()

Rebuild and persist a human-readable synopsis from current facts.

This is a *projection* — always derived from the fact store, never
hand-edited — so it can be regenerated at any time without loss.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

#### save_upload(name, data)

Store a raw uploaded document by filename (see [`add_source()`](#hired.candidate.CandidateKnowledgeBase.add_source)).

* **Return type:**
  [`None`](https://docs.python.org/3/builtins/constants.html#None)

#### sources()

Keys of all raw sources the candidate has provided.

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]

#### supersede(old_fact_id, new_fact)

Replace `old_fact_id` with `new_fact` (invalidate, don’t delete).

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

#### *property* synopsis *: [str](https://docs.python.org/3/builtins/stdtypes.html#str)*

The last persisted synopsis, regenerating it if absent.

#### topic(name)

Get-or-create the dossier for a subject (overview + optional files).

* **Return type:**
  [`TopicDossier`](hired.candidate.topics.html.md#hired.candidate.topics.TopicDossier)

#### topics()

Slugs of all topic dossiers.

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]

### *class* hired.candidate.ConfidenceLevel(\*values)

Bases: [`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Enum`](https://docs.python.org/3/library/enum.html#enum.Enum)

Calibrated confidence in a claim (qualitative, not a raw probability).

### *class* hired.candidate.Fact(\*\*data)

Bases: `BaseModel`

One atomic claim about a candidate.

Atomicity matters: a fact states a single thing so it can be confirmed,
superseded, or cited independently.

#### model_config *: [ClassVar](https://docs.python.org/3/library/typing.html#typing.ClassVar)[ConfigDict]* *= {}*

Configuration for the model, should be a dictionary conforming to [`ConfigDict`][pydantic.config.ConfigDict].

### *class* hired.candidate.FactCategory(\*values)

Bases: [`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Enum`](https://docs.python.org/3/library/enum.html#enum.Enum)

Coarse category for retrieval and synopsis grouping.

### *class* hired.candidate.FactStatus(\*values)

Bases: [`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Enum`](https://docs.python.org/3/library/enum.html#enum.Enum)

Whether a fact is current or has been superseded by a newer one.

### *class* hired.candidate.JDWorkspace(kb, jd_id, , store=None)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Reports, company research, interview-prep briefings, and parsed jobs for one engagement.

```pycon
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
```

#### report_versions(job_id)

Keys of archived prior versions of a job’s report (chronological).

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]

#### save_briefing(key, data)

Persist an interview-prep research briefing (keyed by subject/job).

* **Return type:**
  [`None`](https://docs.python.org/3/builtins/constants.html#None)

#### save_company_report(company, data)

Persist a company/people research report (keyed by company name).

* **Return type:**
  [`None`](https://docs.python.org/3/builtins/constants.html#None)

#### save_report(job_id, data, , archive=True)

Persist the current alignment report, archiving the prior one first.

Archiving (on by default) snapshots any existing report into
`report_history` so the alignment-review agent can diff versions.

* **Return type:**
  [`None`](https://docs.python.org/3/builtins/constants.html#None)

### *class* hired.candidate.MatchState(\*values)

Bases: [`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Enum`](https://docs.python.org/3/library/enum.html#enum.Enum)

Three-valued epistemic state — the core of the honesty contract.

`UNKNOWN` is distinct from `CONTRADICTED`: we have not yet looked, so we
must *ask* rather than assume absence.

### *class* hired.candidate.Provenance(\*\*data)

Bases: `BaseModel`

Where a fact came from, with an optional verbatim supporting quote.

#### model_config *: [ClassVar](https://docs.python.org/3/library/typing.html#typing.ClassVar)[ConfigDict]* *= {}*

Configuration for the model, should be a dictionary conforming to [`ConfigDict`][pydantic.config.ConfigDict].

### *class* hired.candidate.QAEntry(\*\*data)

Bases: `BaseModel`

One clarifying question asked of the candidate and their answer.

Q&A is append-only history; the distilled, updatable projection lives in
[`Fact`](#hired.candidate.Fact) records (linked via `derived_fact_ids`).

#### model_config *: [ClassVar](https://docs.python.org/3/library/typing.html#typing.ClassVar)[ConfigDict]* *= {}*

Configuration for the model, should be a dictionary conforming to [`ConfigDict`][pydantic.config.ConfigDict].

### *class* hired.candidate.RefreshItem(kind, key, content)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

One unit of pending work for a refresh: a changed source or an undistilled Q&A.

### *class* hired.candidate.RefreshProposal(kind, key, records)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Proposed fact records for one item (returned when `apply=False`).

### *class* hired.candidate.RefreshReport(mode, applied, pending=<factory>, proposals=<factory>, added_fact_ids=<factory>, superseded_fact_ids=<factory>)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Outcome (or preview) of a refresh.

### *class* hired.candidate.RefreshState(\*\*data)

Bases: `BaseModel`

The candidate-info refresh ledger (persisted to `user/info/state.json`).

#### model_config *: [ClassVar](https://docs.python.org/3/library/typing.html#typing.ClassVar)[ConfigDict]* *= {}*

Configuration for the model, should be a dictionary conforming to [`ConfigDict`][pydantic.config.ConfigDict].

### *class* hired.candidate.SourceDigest(\*\*data)

Bases: `BaseModel`

What we know about one raw source for change detection + provenance.

#### model_config *: [ClassVar](https://docs.python.org/3/library/typing.html#typing.ClassVar)[ConfigDict]* *= {}*

Configuration for the model, should be a dictionary conforming to [`ConfigDict`][pydantic.config.ConfigDict].

### *class* hired.candidate.SourceKind(\*values)

Bases: [`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Enum`](https://docs.python.org/3/library/enum.html#enum.Enum)

Where a piece of provenance came from.

### *class* hired.candidate.TopicDossier(base_dir, , name=None)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

One subject’s dossier: an `overview.md` plus optional attached files.

```pycon
>>> import tempfile, os
>>> d = TopicDossier(os.path.join(tempfile.mkdtemp(), 'patents'), name='Patents')
>>> d.add_note('Holds 3 US patents on anomaly detection.')
>>> d.overview.splitlines()[0]
'# Patents'
>>> d.add_file('cert.txt', b'patent cert')
>>> d.files()
['cert.txt']
>>> d.get_file('cert.txt')
b'patent cert'
```

#### add_file(filename, data)

Attach a detail file / media blob to the dossier.

* **Return type:**
  [`None`](https://docs.python.org/3/builtins/constants.html#None)

#### add_note(text)

Append a note to the overview (creating it, titled, if absent).

* **Return type:**
  [`None`](https://docs.python.org/3/builtins/constants.html#None)

#### exists()

True once the dossier has an overview or any attached file.

* **Return type:**
  [`bool`](https://docs.python.org/3/builtins/functions.html#bool)

#### files()

Names of attached detail files.

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]

#### *property* overview *: [str](https://docs.python.org/3/builtins/stdtypes.html#str) | [None](https://docs.python.org/3/builtins/constants.html#None)*

The dossier’s overview markdown (the entry point), or `None`.

### hired.candidate.fact_from_record(record, , source_kind, source_id='', subject='me')

Build a (not-yet-persisted) [`Fact`](#hired.candidate.Fact) from a record dict.

* **Return type:**
  [`Fact`](hired.candidate.base.html.md#hired.candidate.base.Fact)

### hired.candidate.ingest_facts(kb, records, , source_kind, source_id='', source_text=None, drop_unverified_quotes=True)

Validate, quote-check, and persist fact records; return persisted ids.

When `source_text` is given, each record’s `quote` is checked to be a
verbatim substring. Unverified quotes are dropped (the fact is still kept,
but without the spurious quote) unless `drop_unverified_quotes` is False,
in which case a `ValueError` is raised — useful for strict pipelines.

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]

### hired.candidate.needs_refresh(kb)

True when there is uningested source/Q&A material — a refresh is warranted.

* **Return type:**
  [`bool`](https://docs.python.org/3/builtins/functions.html#bool)

### hired.candidate.refresh(kb, mode='soft', , ingest_fn=None, apply=True)

Refresh `info` from changed sources + undistilled Q&A. See module docstring.

`ingest_fn(item: RefreshItem) -> list[dict]` supplies the extraction
intelligence (records are the usual `{"statement", "category", "quote", …}`
dicts). With `ingest_fn=None` the report just lists the pending items (the
caller does extraction). With `apply=False` the records are returned as
proposals and nothing is written.

* **Return type:**
  [`RefreshReport`](#hired.candidate.RefreshReport)

### hired.candidate.slug(text)

A filesystem-safe, extension-less key from an arbitrary label.

Used to derive stable store keys from human labels (company names, subjects,
briefing titles) so callers pass natural text and the store stays tidy.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

```pycon
>>> slug('Socure, Inc.')
'socure-inc'
>>> slug('KYC / AML primer')
'kyc-aml-primer'
```

### hired.candidate.verify_quote(quote, source_text)

True if `quote` is a verbatim substring of `source_text`.

A `None` quote (no quote claimed) always verifies. When no source text is
available to check against, we cannot disprove it, so it verifies too — the
invariant only bites when we *can* check.

* **Return type:**
  [`bool`](https://docs.python.org/3/builtins/functions.html#bool)

### Modules

| [`base`](hired.candidate.base.html.md#module-hired.candidate.base)                     | Open-world, provenance-first schemas for accumulated candidate knowledge.           |
|-------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------|
| [`ingest`](hired.candidate.ingest.html.md#module-hired.candidate.ingest)                 | Turn extracted atomic-fact records into persisted, provenance-bearing facts.        |
| [`knowledge_base`](hired.candidate.knowledge_base.html.md#module-hired.candidate.knowledge_base) | The candidate knowledge base: a facade over the user-level store.                   |
| [`state`](hired.candidate.state.html.md#module-hired.candidate.state)                   | Refresh bookkeeping: per-source content digests + last-refresh timestamps.          |
| [`topics`](hired.candidate.topics.html.md#module-hired.candidate.topics)                 | Topic dossiers — "a little, or a whole lot" about any subject the candidate shares. |
| [`workspace`](hired.candidate.workspace.html.md#module-hired.candidate.workspace)           | The per-engagement facade: alignment reports, company research, interview prep.     |
