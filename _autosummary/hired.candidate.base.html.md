# hired.candidate.base

Open-world, provenance-first schemas for accumulated candidate knowledge.

The governing principle (see `misc/docs/DESIGN.md` §5): the **absence** of a
fact is never a negative claim. Only an explicit fact whose `match_state` is
`CONTRADICTED` asserts that the candidate lacks something. Silence is
`UNKNOWN` — a prompt to *ask*, not a gap.

Every [`Fact`](#hired.candidate.base.Fact) carries [`Provenance`](#hired.candidate.base.Provenance). When a provenance `quote` is
drawn from a text source it MUST be a verbatim substring of that source — an
anti-hallucination invariant enforced at extraction time.

### Functions

| [`slug`](#hired.candidate.base.slug)(text)   | A filesystem-safe, extension-less key from an arbitrary label.   |
|---------------------------------------------------------------|------------------------------------------------------------------|

### Classes

| [`ConfidenceLevel`](#hired.candidate.base.ConfidenceLevel)(\*values)   | Calibrated confidence in a claim (qualitative, not a raw probability).   |
|------------------------------------------------------------------------------|--------------------------------------------------------------------------|
| [`Fact`](#hired.candidate.base.Fact)(\*\*data)              | One atomic claim about a candidate.                                      |
| [`FactCategory`](#hired.candidate.base.FactCategory)(\*values)      | Coarse category for retrieval and synopsis grouping.                     |
| [`FactStatus`](#hired.candidate.base.FactStatus)(\*values)        | Whether a fact is current or has been superseded by a newer one.         |
| [`MatchState`](#hired.candidate.base.MatchState)(\*values)        | Three-valued epistemic state — the core of the honesty contract.         |
| [`Provenance`](#hired.candidate.base.Provenance)(\*\*data)        | Where a fact came from, with an optional verbatim supporting quote.      |
| [`QAEntry`](#hired.candidate.base.QAEntry)(\*\*data)           | One clarifying question asked of the candidate and their answer.         |
| [`SourceKind`](#hired.candidate.base.SourceKind)(\*values)        | Where a piece of provenance came from.                                   |

### *class* hired.candidate.base.ConfidenceLevel(\*values)

Bases: [`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Enum`](https://docs.python.org/3/library/enum.html#enum.Enum)

Calibrated confidence in a claim (qualitative, not a raw probability).

### *class* hired.candidate.base.Fact(\*\*data)

Bases: `BaseModel`

One atomic claim about a candidate.

Atomicity matters: a fact states a single thing so it can be confirmed,
superseded, or cited independently.

#### model_config *: [ClassVar](https://docs.python.org/3/library/typing.html#typing.ClassVar)[ConfigDict]* *= {}*

Configuration for the model, should be a dictionary conforming to [`ConfigDict`][pydantic.config.ConfigDict].

### *class* hired.candidate.base.FactCategory(\*values)

Bases: [`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Enum`](https://docs.python.org/3/library/enum.html#enum.Enum)

Coarse category for retrieval and synopsis grouping.

### *class* hired.candidate.base.FactStatus(\*values)

Bases: [`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Enum`](https://docs.python.org/3/library/enum.html#enum.Enum)

Whether a fact is current or has been superseded by a newer one.

### *class* hired.candidate.base.MatchState(\*values)

Bases: [`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Enum`](https://docs.python.org/3/library/enum.html#enum.Enum)

Three-valued epistemic state — the core of the honesty contract.

`UNKNOWN` is distinct from `CONTRADICTED`: we have not yet looked, so we
must *ask* rather than assume absence.

### *class* hired.candidate.base.Provenance(\*\*data)

Bases: `BaseModel`

Where a fact came from, with an optional verbatim supporting quote.

#### model_config *: [ClassVar](https://docs.python.org/3/library/typing.html#typing.ClassVar)[ConfigDict]* *= {}*

Configuration for the model, should be a dictionary conforming to [`ConfigDict`][pydantic.config.ConfigDict].

### *class* hired.candidate.base.QAEntry(\*\*data)

Bases: `BaseModel`

One clarifying question asked of the candidate and their answer.

Q&A is append-only history; the distilled, updatable projection lives in
[`Fact`](#hired.candidate.base.Fact) records (linked via `derived_fact_ids`).

#### model_config *: [ClassVar](https://docs.python.org/3/library/typing.html#typing.ClassVar)[ConfigDict]* *= {}*

Configuration for the model, should be a dictionary conforming to [`ConfigDict`][pydantic.config.ConfigDict].

### *class* hired.candidate.base.SourceKind(\*values)

Bases: [`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Enum`](https://docs.python.org/3/library/enum.html#enum.Enum)

Where a piece of provenance came from.

### hired.candidate.base.slug(text)

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
