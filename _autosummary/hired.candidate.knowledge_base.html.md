# hired.candidate.knowledge_base

The candidate knowledge base: a facade over the user-level store.

[`CandidateKnowledgeBase`](#hired.candidate.knowledge_base.CandidateKnowledgeBase) is the domain-driven entry point for accumulating
and querying knowledge about one candidate — *what is true about them*, reusable
across every job application. It wraps the [`UserStore`](hired.persistence.base.html.md#hired.persistence.base.UserStore)
with validated, intention-revealing methods (`add_fact`, `facts`, `record_qa`,
`save_upload`, …) and keeps a regenerated, human-readable `synopsis()`
projection of the fact store for fast context loading.

Work tied to a specific company’s role(s) — alignment reports, company research,
interview prep — does **not** live here; it lives in a per-engagement
[`JDWorkspace`](hired.candidate.workspace.html.md#hired.candidate.workspace.JDWorkspace), reached via `jd()`.

### Classes

| [`CandidateKnowledgeBase`](#hired.candidate.knowledge_base.CandidateKnowledgeBase)([user, store])   | Accumulated, open-world knowledge about a single candidate (user-level).   |
|------------------------------------------------------------------------------------------|----------------------------------------------------------------------------|

### *class* hired.candidate.knowledge_base.CandidateKnowledgeBase(user='me', , store=None)

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
[`hired.candidate.refresh`](hired.candidate.html.md#hired.candidate.refresh).

* **Return type:**
  [`RefreshReport`](hired.candidate.html.md#hired.candidate.RefreshReport)

#### regenerate_synopsis()

Rebuild and persist a human-readable synopsis from current facts.

This is a *projection* — always derived from the fact store, never
hand-edited — so it can be regenerated at any time without loss.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

#### save_upload(name, data)

Store a raw uploaded document by filename (see [`add_source()`](#hired.candidate.knowledge_base.CandidateKnowledgeBase.add_source)).

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
