# hired.candidate.state

Refresh bookkeeping: per-source content digests + last-refresh timestamps.

Records a content digest for every raw source the candidate has provided, so a
later refresh can tell which sources are *new* or *changed* since they were last
ingested — without re-reading everything. The state is a singleton persisted at
`user/info/state.json` and is the shared substrate for raw-source tracking
([`add_source()`](hired.candidate.knowledge_base.html.md#hired.candidate.knowledge_base.CandidateKnowledgeBase.add_source)) and
the soft/hard refresh loop.

### Functions

| [`load_state`](#hired.candidate.state.load_state)(user_store)        | Read the refresh state for a `UserStore` (empty if none yet).   |
|--------------------------------------------------------------------------------|-----------------------------------------------------------------|
| [`save_state`](#hired.candidate.state.save_state)(user_store, state) | Persist the refresh state for a `UserStore`.                    |
| [`sha256_hex`](#hired.candidate.state.sha256_hex)(data)              | Content hash used as the change signal for a raw source.        |

### Classes

| [`RefreshState`](#hired.candidate.state.RefreshState)(\*\*data)   | The candidate-info refresh ledger (persisted to `user/info/state.json`).   |
|---------------------------------------------------------------------------|----------------------------------------------------------------------------|
| [`SourceDigest`](#hired.candidate.state.SourceDigest)(\*\*data)   | What we know about one raw source for change detection + provenance.       |

### *class* hired.candidate.state.RefreshState(\*\*data)

Bases: `BaseModel`

The candidate-info refresh ledger (persisted to `user/info/state.json`).

#### model_config *: [ClassVar](https://docs.python.org/3/library/typing.html#typing.ClassVar)[ConfigDict]* *= {}*

Configuration for the model, should be a dictionary conforming to [`ConfigDict`][pydantic.config.ConfigDict].

### *class* hired.candidate.state.SourceDigest(\*\*data)

Bases: `BaseModel`

What we know about one raw source for change detection + provenance.

#### model_config *: [ClassVar](https://docs.python.org/3/library/typing.html#typing.ClassVar)[ConfigDict]* *= {}*

Configuration for the model, should be a dictionary conforming to [`ConfigDict`][pydantic.config.ConfigDict].

### hired.candidate.state.load_state(user_store)

Read the refresh state for a `UserStore` (empty if none yet).

* **Return type:**
  [`RefreshState`](#hired.candidate.state.RefreshState)

### hired.candidate.state.save_state(user_store, state)

Persist the refresh state for a `UserStore`.

* **Return type:**
  [`None`](https://docs.python.org/3/builtins/constants.html#None)

### hired.candidate.state.sha256_hex(data)

Content hash used as the change signal for a raw source.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)
