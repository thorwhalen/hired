# hired.alignment

JD-vs-candidate alignment: classify each requirement honestly into four buckets.

Public surface:

- schemas in [`hired.alignment.base`](hired.alignment.base.html.md#module-hired.alignment.base) ([`Requirement`](#hired.alignment.Requirement),
  [`RequirementRecord`](#hired.alignment.RequirementRecord), [`AlignmentReport`](#hired.alignment.AlignmentReport), and the enums),
- the deterministic rubric in [`hired.alignment.rubric`](hired.alignment.rubric.html.md#module-hired.alignment.rubric)
  ([`classify()`](#hired.alignment.classify), [`assign_bucket()`](#hired.alignment.assign_bucket), [`apply_ai_leverage()`](#hired.alignment.apply_ai_leverage)),
- the elicitation helpers in [`hired.alignment.elicitation`](hired.alignment.elicitation.html.md#module-hired.alignment.elicitation)
  ([`rank_clarifications()`](#hired.alignment.rank_clarifications), [`is_decision_stable()`](#hired.alignment.is_decision_stable)),
- Markdown rendering in [`hired.alignment.report`](hired.alignment.report.html.md#module-hired.alignment.report)
  ([`render_report_markdown()`](#hired.alignment.render_report_markdown)).

The *intelligence* (judging transfer distance, trainability, evidence) is supplied
by the `hired-align` skill (Claude as brain) or an injected LLM; this package
provides the schemas, deterministic scoring, and rendering. See
`misc/docs/DESIGN.md` §6-8.

### Functions

| [`classify`](#hired.alignment.classify)(record)                                  | Fill `gap_size` and `bucket` (and `needs_clarification`) in place.                                        |
|----------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------|
| [`assign_bucket`](#hired.alignment.assign_bucket)(record)                             | Assign the alignment bucket for a record, or `None` if it should be a clarifying question instead.        |
| [`apply_ai_leverage`](#hired.alignment.apply_ai_leverage)(closeability, ai_leverage, ...) | Soften a *codified* gap's closeability by the candidate's AI leverage.                                    |
| [`compute_gap_size`](#hired.alignment.compute_gap_size)(required_level, candidate_level) | Residual gap, floored at zero.                                                                            |
| [`rank_clarifications`](#hired.alignment.rank_clarifications)(records, \*[, ...])           | Produce clarifying questions for askable records, highest info-gain first.                                |
| [`is_decision_stable`](#hired.alignment.is_decision_stable)(records)                       | True when no remaining open unknown could flip the verdict.                                               |
| [`should_ask`](#hired.alignment.should_ask)(record)                                | Whether to route this record to a clarifying question.                                                    |
| [`info_gain`](#hired.alignment.info_gain)(record)                                 | Expected information gain of resolving this requirement, wrt the verdict.                                 |
| [`render_report_markdown`](#hired.alignment.render_report_markdown)(report)                    | Render the report as a Markdown string.                                                                   |
| [`diff_reports`](#hired.alignment.diff_reports)(old, new)                            | Return a structured diff of two alignment-report dicts.                                                   |
| [`summarize_diff`](#hired.alignment.summarize_diff)(diff)                              | A short human-readable summary of [`diff_reports()`](#hired.alignment.diff_reports) output. |

### Classes

| [`Requirement`](#hired.alignment.Requirement)(\*\*data)       | One atomic requirement extracted verbatim from a job description.        |
|------------------------------------------------------------------------------|--------------------------------------------------------------------------|
| [`RequirementRecord`](#hired.alignment.RequirementRecord)(\*\*data) | The analysis of one requirement against the candidate's knowledge.       |
| [`Evidence`](#hired.alignment.Evidence)(\*\*data)          | A verbatim grounding span for a match judgment.                          |
| [`AlignmentReport`](#hired.alignment.AlignmentReport)(\*\*data)   | A complete, verdict-first alignment analysis for one JD.                 |
| [`Verdict`](#hired.alignment.Verdict)(\*\*data)           |                                                                          |
| [`ScoreSummary`](#hired.alignment.ScoreSummary)(\*\*data)      |                                                                          |
| [`NextAction`](#hired.alignment.NextAction)(\*\*data)        |                                                                          |
| [`Clarification`](#hired.alignment.Clarification)(\*\*data)     | A question to ask the candidate to resolve a decision-relevant unknown.  |
| [`InterviewPrep`](#hired.alignment.InterviewPrep)(\*\*data)     |                                                                          |
| [`Bucket`](#hired.alignment.Bucket)(\*values)            | The four alignment buckets.                                              |
| [`MatchType`](#hired.alignment.MatchType)(\*values)         | How the candidate's background relates to the requirement (Axis A).      |
| [`RequirementClass`](#hired.alignment.RequirementClass)(\*values)  | How decision-critical a requirement is.                                  |
| [`SkillType`](#hired.alignment.SkillType)(\*values)         |                                                                          |
| [`Closeability`](#hired.alignment.Closeability)(\*values)      | How hard a gap is to close (Axis B), after the AI-leverage modifier.     |
| [`CloseMethod`](#hired.alignment.CloseMethod)(\*values)       |                                                                          |
| [`TimeToClose`](#hired.alignment.TimeToClose)(\*values)       |                                                                          |
| [`Transferability`](#hired.alignment.Transferability)(\*values)   |                                                                          |
| [`AILeverage`](#hired.alignment.AILeverage)(\*values)        | How much the candidate's standing AI-agent capability lowers the ramp.   |
| [`FieldCompleteness`](#hired.alignment.FieldCompleteness)(\*values) | Local closed-world flag: may a missing value be read as a real negative? |
| [`Recommendation`](#hired.alignment.Recommendation)(\*values)    |                                                                          |
| [`FitBand`](#hired.alignment.FitBand)(\*values)           |                                                                          |

### *class* hired.alignment.AILeverage(\*values)

Bases: [`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Enum`](https://docs.python.org/3/library/enum.html#enum.Enum)

How much the candidate’s standing AI-agent capability lowers the ramp.

Applies to *codified / knowledge-breadth* gaps, not tacit-judgment or
enduring-aptitude gaps (those it cannot rescue).

### *class* hired.alignment.AlignmentReport(\*\*data)

Bases: `BaseModel`

A complete, verdict-first alignment analysis for one JD.

#### model_config *: [ClassVar](https://docs.python.org/3/library/typing.html#typing.ClassVar)[ConfigDict]* *= {}*

Configuration for the model, should be a dictionary conforming to [`ConfigDict`][pydantic.config.ConfigDict].

### *class* hired.alignment.Bucket(\*values)

Bases: [`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Enum`](https://docs.python.org/3/library/enum.html#enum.Enum)

The four alignment buckets.

### *class* hired.alignment.Clarification(\*\*data)

Bases: `BaseModel`

A question to ask the candidate to resolve a decision-relevant unknown.

#### model_config *: [ClassVar](https://docs.python.org/3/library/typing.html#typing.ClassVar)[ConfigDict]* *= {}*

Configuration for the model, should be a dictionary conforming to [`ConfigDict`][pydantic.config.ConfigDict].

### *class* hired.alignment.CloseMethod(\*values)

Bases: [`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Enum`](https://docs.python.org/3/library/enum.html#enum.Enum)

### *class* hired.alignment.Closeability(\*values)

Bases: [`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Enum`](https://docs.python.org/3/library/enum.html#enum.Enum)

How hard a gap is to close (Axis B), after the AI-leverage modifier.

### *class* hired.alignment.Evidence(\*\*data)

Bases: `BaseModel`

A verbatim grounding span for a match judgment.

#### model_config *: [ClassVar](https://docs.python.org/3/library/typing.html#typing.ClassVar)[ConfigDict]* *= {}*

Configuration for the model, should be a dictionary conforming to [`ConfigDict`][pydantic.config.ConfigDict].

### *class* hired.alignment.FieldCompleteness(\*values)

Bases: [`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Enum`](https://docs.python.org/3/library/enum.html#enum.Enum)

Local closed-world flag: may a missing value be read as a real negative?

### *class* hired.alignment.FitBand(\*values)

Bases: [`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Enum`](https://docs.python.org/3/library/enum.html#enum.Enum)

### *class* hired.alignment.InterviewPrep(\*\*data)

Bases: `BaseModel`

#### model_config *: [ClassVar](https://docs.python.org/3/library/typing.html#typing.ClassVar)[ConfigDict]* *= {}*

Configuration for the model, should be a dictionary conforming to [`ConfigDict`][pydantic.config.ConfigDict].

### *class* hired.alignment.MatchType(\*values)

Bases: [`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Enum`](https://docs.python.org/3/library/enum.html#enum.Enum)

How the candidate’s background relates to the requirement (Axis A).

### *class* hired.alignment.NextAction(\*\*data)

Bases: `BaseModel`

#### model_config *: [ClassVar](https://docs.python.org/3/library/typing.html#typing.ClassVar)[ConfigDict]* *= {}*

Configuration for the model, should be a dictionary conforming to [`ConfigDict`][pydantic.config.ConfigDict].

### *class* hired.alignment.Recommendation(\*values)

Bases: [`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Enum`](https://docs.python.org/3/library/enum.html#enum.Enum)

### *class* hired.alignment.Requirement(\*\*data)

Bases: `BaseModel`

One atomic requirement extracted verbatim from a job description.

#### model_config *: [ClassVar](https://docs.python.org/3/library/typing.html#typing.ClassVar)[ConfigDict]* *= {}*

Configuration for the model, should be a dictionary conforming to [`ConfigDict`][pydantic.config.ConfigDict].

### *class* hired.alignment.RequirementClass(\*values)

Bases: [`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Enum`](https://docs.python.org/3/library/enum.html#enum.Enum)

How decision-critical a requirement is.

### *class* hired.alignment.RequirementRecord(\*\*data)

Bases: `BaseModel`

The analysis of one requirement against the candidate’s knowledge.

#### model_config *: [ClassVar](https://docs.python.org/3/library/typing.html#typing.ClassVar)[ConfigDict]* *= {}*

Configuration for the model, should be a dictionary conforming to [`ConfigDict`][pydantic.config.ConfigDict].

### *class* hired.alignment.ScoreSummary(\*\*data)

Bases: `BaseModel`

#### model_config *: [ClassVar](https://docs.python.org/3/library/typing.html#typing.ClassVar)[ConfigDict]* *= {}*

Configuration for the model, should be a dictionary conforming to [`ConfigDict`][pydantic.config.ConfigDict].

### *class* hired.alignment.SkillType(\*values)

Bases: [`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Enum`](https://docs.python.org/3/library/enum.html#enum.Enum)

### *class* hired.alignment.TimeToClose(\*values)

Bases: [`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Enum`](https://docs.python.org/3/library/enum.html#enum.Enum)

### *class* hired.alignment.Transferability(\*values)

Bases: [`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Enum`](https://docs.python.org/3/library/enum.html#enum.Enum)

### *class* hired.alignment.Verdict(\*\*data)

Bases: `BaseModel`

#### model_config *: [ClassVar](https://docs.python.org/3/library/typing.html#typing.ClassVar)[ConfigDict]* *= {}*

Configuration for the model, should be a dictionary conforming to [`ConfigDict`][pydantic.config.ConfigDict].

### hired.alignment.apply_ai_leverage(closeability, ai_leverage, , skill_type, is_tacit=False)

Soften a *codified* gap’s closeability by the candidate’s AI leverage.

Tacit/soft gaps and structurally-hard gaps are never softened — AI agents
extend *breadth of codified knowledge*, not judgment or enduring aptitude.

* **Return type:**
  [`Closeability`](hired.alignment.base.html.md#hired.alignment.base.Closeability)

```pycon
>>> apply_ai_leverage(Closeability.REQUIRES_EXPERIENCE, AILeverage.HIGH,
...                    skill_type=SkillType.TECHNICAL)
<Closeability.LEARNABLE: 'learnable'>
>>> apply_ai_leverage(Closeability.REQUIRES_EXPERIENCE, AILeverage.HIGH,
...                    skill_type=SkillType.SOFT_SKILL)
<Closeability.REQUIRES_EXPERIENCE: 'requires_experience'>
```

### hired.alignment.assign_bucket(record)

Assign the alignment bucket for a record, or `None` if it should be a
clarifying question instead.

Returns `None` when the requirement is `UNKNOWN` on an OPEN field — that
routes to elicitation rather than being scored as a gap (the “don’t assume
absence” rule). `UNKNOWN` on a CLOSED field is treated as a real gap.

* **Return type:**
  [`Bucket`](hired.alignment.base.html.md#hired.alignment.base.Bucket) | [`None`](https://docs.python.org/3/builtins/constants.html#None)

### hired.alignment.classify(record)

Fill `gap_size` and `bucket` (and `needs_clarification`) in place.

Returns the same record for convenience.

* **Return type:**
  [`RequirementRecord`](hired.alignment.base.html.md#hired.alignment.base.RequirementRecord)

### hired.alignment.compute_gap_size(required_level, candidate_level)

Residual gap, floored at zero.

* **Return type:**
  [`int`](https://docs.python.org/3/builtins/functions.html#int)

### hired.alignment.diff_reports(old, new)

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

### hired.alignment.info_gain(record)

Expected information gain of resolving this requirement, wrt the verdict.

Heuristic: `uncertainty × criticality`. An `impact` override (1-5) scales
criticality when the analyst has a sharper view than the requirement class.

* **Return type:**
  [`float`](https://docs.python.org/3/builtins/functions.html#float)

### hired.alignment.is_decision_stable(records)

True when no remaining open unknown could flip the verdict.

Concretely: there are no askable (decision-relevant, open, unknown)
requirements left. This is the sharpest stop criterion from the research.

* **Return type:**
  [`bool`](https://docs.python.org/3/builtins/functions.html#bool)

### hired.alignment.rank_clarifications(records, , max_questions=None, min_info_gain=0.0)

Produce clarifying questions for askable records, highest info-gain first.

The question *text* is left to the analyst; this returns the prioritized
skeleton (requirement, reason, info_gain) so the caller can fill `question`.

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`Clarification`](hired.alignment.base.html.md#hired.alignment.base.Clarification)]

### hired.alignment.render_report_markdown(report)

Render the report as a Markdown string.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### hired.alignment.should_ask(record)

Whether to route this record to a clarifying question.

Ask only when it’s `UNKNOWN` on an OPEN field and decision-relevant — the
“don’t assume absence from silence” rule. CONTRADICTED facts and closed-field
unknowns are real gaps, not questions.

* **Return type:**
  [`bool`](https://docs.python.org/3/builtins/functions.html#bool)

### hired.alignment.summarize_diff(diff)

A short human-readable summary of [`diff_reports()`](#hired.alignment.diff_reports) output.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### Modules

| [`base`](hired.alignment.base.html.md#module-hired.alignment.base)               | Schemas for JD-vs-candidate alignment analysis.                                                                              |
|-------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------|
| [`diff`](hired.alignment.diff.html.md#module-hired.alignment.diff)               | Deterministic diff between two alignment reports.                                                                            |
| [`elicitation`](hired.alignment.elicitation.html.md#module-hired.alignment.elicitation) | The honesty loop: rank unknowns into the most informative questions first.                                                   |
| [`report`](hired.alignment.report.html.md#module-hired.alignment.report)           | Render an [`AlignmentReport`](hired.alignment.base.html.md#hired.alignment.base.AlignmentReport) to Markdown. |
| [`rubric`](hired.alignment.rubric.html.md#module-hired.alignment.rubric)           | Deterministic bucket assignment — the two-axis rubric in code.                                                               |
