# hired.alignment.base

Schemas for JD-vs-candidate alignment analysis.

A job description is decomposed into [`Requirement`](#hired.alignment.base.Requirement) records; each is
analysed into a [`RequirementRecord`](#hired.alignment.base.RequirementRecord) carrying a three-valued
[`MatchState`](hired.candidate.base.html.md#hired.candidate.base.MatchState), a [`Bucket`](#hired.alignment.base.Bucket), grounding
[`Evidence`](#hired.alignment.base.Evidence), and the fields the elicitation loop needs. The whole analysis
is an [`AlignmentReport`](#hired.alignment.base.AlignmentReport) — verdict-first, evidence-quoted, banded (never a
single false-precision percentage).

See `misc/docs/DESIGN.md` §6.

### Classes

| [`AILeverage`](#hired.alignment.base.AILeverage)(\*values)        | How much the candidate's standing AI-agent capability lowers the ramp.   |
|------------------------------------------------------------------------------|--------------------------------------------------------------------------|
| [`AlignmentReport`](#hired.alignment.base.AlignmentReport)(\*\*data)   | A complete, verdict-first alignment analysis for one JD.                 |
| [`Bucket`](#hired.alignment.base.Bucket)(\*values)            | The four alignment buckets.                                              |
| [`Clarification`](#hired.alignment.base.Clarification)(\*\*data)     | A question to ask the candidate to resolve a decision-relevant unknown.  |
| [`CloseMethod`](#hired.alignment.base.CloseMethod)(\*values)       |                                                                          |
| [`Closeability`](#hired.alignment.base.Closeability)(\*values)      | How hard a gap is to close (Axis B), after the AI-leverage modifier.     |
| [`Evidence`](#hired.alignment.base.Evidence)(\*\*data)          | A verbatim grounding span for a match judgment.                          |
| [`FieldCompleteness`](#hired.alignment.base.FieldCompleteness)(\*values) | Local closed-world flag: may a missing value be read as a real negative? |
| [`FitBand`](#hired.alignment.base.FitBand)(\*values)           |                                                                          |
| [`InterviewPrep`](#hired.alignment.base.InterviewPrep)(\*\*data)     |                                                                          |
| [`MatchType`](#hired.alignment.base.MatchType)(\*values)         | How the candidate's background relates to the requirement (Axis A).      |
| [`NextAction`](#hired.alignment.base.NextAction)(\*\*data)        |                                                                          |
| [`Recommendation`](#hired.alignment.base.Recommendation)(\*values)    |                                                                          |
| [`Requirement`](#hired.alignment.base.Requirement)(\*\*data)       | One atomic requirement extracted verbatim from a job description.        |
| [`RequirementClass`](#hired.alignment.base.RequirementClass)(\*values)  | How decision-critical a requirement is.                                  |
| [`RequirementRecord`](#hired.alignment.base.RequirementRecord)(\*\*data) | The analysis of one requirement against the candidate's knowledge.       |
| [`ScoreSummary`](#hired.alignment.base.ScoreSummary)(\*\*data)      |                                                                          |
| [`SkillType`](#hired.alignment.base.SkillType)(\*values)         |                                                                          |
| [`TimeToClose`](#hired.alignment.base.TimeToClose)(\*values)       |                                                                          |
| [`Transferability`](#hired.alignment.base.Transferability)(\*values)   |                                                                          |
| [`Verdict`](#hired.alignment.base.Verdict)(\*\*data)           |                                                                          |

### *class* hired.alignment.base.AILeverage(\*values)

Bases: [`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Enum`](https://docs.python.org/3/library/enum.html#enum.Enum)

How much the candidate’s standing AI-agent capability lowers the ramp.

Applies to *codified / knowledge-breadth* gaps, not tacit-judgment or
enduring-aptitude gaps (those it cannot rescue).

### *class* hired.alignment.base.AlignmentReport(\*\*data)

Bases: `BaseModel`

A complete, verdict-first alignment analysis for one JD.

#### model_config *: [ClassVar](https://docs.python.org/3/library/typing.html#typing.ClassVar)[ConfigDict]* *= {}*

Configuration for the model, should be a dictionary conforming to [`ConfigDict`][pydantic.config.ConfigDict].

### *class* hired.alignment.base.Bucket(\*values)

Bases: [`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Enum`](https://docs.python.org/3/library/enum.html#enum.Enum)

The four alignment buckets.

### *class* hired.alignment.base.Clarification(\*\*data)

Bases: `BaseModel`

A question to ask the candidate to resolve a decision-relevant unknown.

#### model_config *: [ClassVar](https://docs.python.org/3/library/typing.html#typing.ClassVar)[ConfigDict]* *= {}*

Configuration for the model, should be a dictionary conforming to [`ConfigDict`][pydantic.config.ConfigDict].

### *class* hired.alignment.base.CloseMethod(\*values)

Bases: [`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Enum`](https://docs.python.org/3/library/enum.html#enum.Enum)

### *class* hired.alignment.base.Closeability(\*values)

Bases: [`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Enum`](https://docs.python.org/3/library/enum.html#enum.Enum)

How hard a gap is to close (Axis B), after the AI-leverage modifier.

### *class* hired.alignment.base.Evidence(\*\*data)

Bases: `BaseModel`

A verbatim grounding span for a match judgment.

#### model_config *: [ClassVar](https://docs.python.org/3/library/typing.html#typing.ClassVar)[ConfigDict]* *= {}*

Configuration for the model, should be a dictionary conforming to [`ConfigDict`][pydantic.config.ConfigDict].

### *class* hired.alignment.base.FieldCompleteness(\*values)

Bases: [`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Enum`](https://docs.python.org/3/library/enum.html#enum.Enum)

Local closed-world flag: may a missing value be read as a real negative?

### *class* hired.alignment.base.FitBand(\*values)

Bases: [`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Enum`](https://docs.python.org/3/library/enum.html#enum.Enum)

### *class* hired.alignment.base.InterviewPrep(\*\*data)

Bases: `BaseModel`

#### model_config *: [ClassVar](https://docs.python.org/3/library/typing.html#typing.ClassVar)[ConfigDict]* *= {}*

Configuration for the model, should be a dictionary conforming to [`ConfigDict`][pydantic.config.ConfigDict].

### *class* hired.alignment.base.MatchType(\*values)

Bases: [`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Enum`](https://docs.python.org/3/library/enum.html#enum.Enum)

How the candidate’s background relates to the requirement (Axis A).

### *class* hired.alignment.base.NextAction(\*\*data)

Bases: `BaseModel`

#### model_config *: [ClassVar](https://docs.python.org/3/library/typing.html#typing.ClassVar)[ConfigDict]* *= {}*

Configuration for the model, should be a dictionary conforming to [`ConfigDict`][pydantic.config.ConfigDict].

### *class* hired.alignment.base.Recommendation(\*values)

Bases: [`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Enum`](https://docs.python.org/3/library/enum.html#enum.Enum)

### *class* hired.alignment.base.Requirement(\*\*data)

Bases: `BaseModel`

One atomic requirement extracted verbatim from a job description.

#### model_config *: [ClassVar](https://docs.python.org/3/library/typing.html#typing.ClassVar)[ConfigDict]* *= {}*

Configuration for the model, should be a dictionary conforming to [`ConfigDict`][pydantic.config.ConfigDict].

### *class* hired.alignment.base.RequirementClass(\*values)

Bases: [`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Enum`](https://docs.python.org/3/library/enum.html#enum.Enum)

How decision-critical a requirement is.

### *class* hired.alignment.base.RequirementRecord(\*\*data)

Bases: `BaseModel`

The analysis of one requirement against the candidate’s knowledge.

#### model_config *: [ClassVar](https://docs.python.org/3/library/typing.html#typing.ClassVar)[ConfigDict]* *= {}*

Configuration for the model, should be a dictionary conforming to [`ConfigDict`][pydantic.config.ConfigDict].

### *class* hired.alignment.base.ScoreSummary(\*\*data)

Bases: `BaseModel`

#### model_config *: [ClassVar](https://docs.python.org/3/library/typing.html#typing.ClassVar)[ConfigDict]* *= {}*

Configuration for the model, should be a dictionary conforming to [`ConfigDict`][pydantic.config.ConfigDict].

### *class* hired.alignment.base.SkillType(\*values)

Bases: [`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Enum`](https://docs.python.org/3/library/enum.html#enum.Enum)

### *class* hired.alignment.base.TimeToClose(\*values)

Bases: [`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Enum`](https://docs.python.org/3/library/enum.html#enum.Enum)

### *class* hired.alignment.base.Transferability(\*values)

Bases: [`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Enum`](https://docs.python.org/3/library/enum.html#enum.Enum)

### *class* hired.alignment.base.Verdict(\*\*data)

Bases: `BaseModel`

#### model_config *: [ClassVar](https://docs.python.org/3/library/typing.html#typing.ClassVar)[ConfigDict]* *= {}*

Configuration for the model, should be a dictionary conforming to [`ConfigDict`][pydantic.config.ConfigDict].
