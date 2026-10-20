# hired.alignment

JD-vs-candidate alignment: classify each requirement honestly into four buckets.

Public surface:

- schemas in [`hired.alignment.base`](hired.alignment.base.html.md#module-hired.alignment.base) ([`Requirement`](#hired.alignment.Requirement),
  [`RequirementRecord`](#hired.alignment.RequirementRecord), [`AlignmentReport`](#hired.alignment.AlignmentReport), and the enums),
- the deterministic rubric in [`hired.alignment.rubric`](hired.alignment.rubric.html.md#module-hired.alignment.rubric)
  ([`classify()`](#hired.alignment.classify), [`assign_bucket()`](#hired.alignment.assign_bucket), [`apply_ai_leverage()`](#hired.alignment.apply_ai_leverage)),
- the elicitation helpers in [`hired.alignment.elicitation`](hired.alignment.elicitation.html.md#module-hired.alignment.elicitation)
  ([`rank_clarifications()`](#hired.alignment.rank_clarifications), [`is_decision_stable()`](#hired.alignment.is_decision_stable)),
- calibrated confidence in [`hired.alignment.calibration`](hired.alignment.calibration.html.md#module-hired.alignment.calibration)
  ([`semantic_consistency()`](#hired.alignment.semantic_consistency), [`calibrate_match()`](#hired.alignment.calibrate_match) and its conformal
  [`MatchCalibrator`](#hired.alignment.MatchCalibrator) ask/auto-decide rule),
- deterministic report finalization in [`hired.alignment.assemble`](hired.alignment.assemble.html.md#module-hired.alignment.assemble)
  ([`finalize_report()`](#hired.alignment.finalize_report) — reclassify, recount, rebuild blockers/clarifications),
- the injected-LLM analyzer in [`hired.alignment.analyzer`](hired.alignment.analyzer.html.md#module-hired.alignment.analyzer)
  ([`LLMAlignmentAnalyzer`](#hired.alignment.LLMAlignmentAnalyzer), [`analyze_jd()`](#hired.alignment.analyze_jd) — decompose, retrieve,
  quote-then-answer, grounding gate, deterministic [`aggregate_verdict()`](#hired.alignment.aggregate_verdict)),
- rendering in [`hired.alignment.report`](hired.alignment.report.html.md#module-hired.alignment.report) ([`render_report()`](#hired.alignment.render_report) dispatching to
  [`render_report_markdown()`](#hired.alignment.render_report_markdown) / [`render_report_html()`](#hired.alignment.render_report_html)).

The *intelligence* (judging transfer distance, trainability, evidence) is supplied
by the `hired-align` skill (Claude as brain) or an injected LLM; this package
provides the schemas, deterministic scoring, and rendering. See
`misc/docs/DESIGN.md` §6-8.

### Functions

| [`classify`](#hired.alignment.classify)(record)                                  | Fill `gap_size` and `bucket` (and `needs_clarification`) in place.                                                                      |
|----------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------|
| [`assign_bucket`](#hired.alignment.assign_bucket)(record)                             | Assign the alignment bucket for a record, or `None` if it should be a clarifying question instead.                                      |
| [`apply_ai_leverage`](#hired.alignment.apply_ai_leverage)(closeability, ai_leverage, ...) | Soften a *codified* gap's closeability by the candidate's AI leverage.                                                                  |
| [`compute_gap_size`](#hired.alignment.compute_gap_size)(required_level, candidate_level) | Residual gap, floored at zero.                                                                                                          |
| [`rank_clarifications`](#hired.alignment.rank_clarifications)(records, \*[, ...])           | Produce clarifying questions for askable records, highest info-gain first.                                                              |
| [`is_decision_stable`](#hired.alignment.is_decision_stable)(records)                       | True when no remaining open unknown could flip the verdict.                                                                             |
| [`should_ask`](#hired.alignment.should_ask)(record)                                | Whether to route this record to a clarifying question.                                                                                  |
| [`info_gain`](#hired.alignment.info_gain)(record)                                 | Expected information gain of resolving this requirement, wrt the verdict.                                                               |
| [`semantic_consistency`](#hired.alignment.semantic_consistency)(samples, \*[, meaning])      | The agreement of sampled answers, clustered by `meaning` (default: equality).                                                           |
| [`match_share`](#hired.alignment.match_share)(samples, \*[, is_match])              | The share of sampled judgments that say "match": a score in `[0, 1]`.                                                                   |
| [`confidence_level`](#hired.alignment.confidence_level)(agreement, \*[, high, medium])   | A `ConfidenceLevel` from sampled agreement rather than self-report.                                                                     |
| [`calibrate_match`](#hired.alignment.calibrate_match)(scores, labels, \*[, ...])        | Fit the ask/auto-decide rule on held-out judgments with known truth.                                                                    |
| [`apply_calibration`](#hired.alignment.apply_calibration)(record, samples, \*[, ...])     | Set `record`'s confidence from sampled judgments, and its decision if calibrated.                                                       |
| [`finalize_report`](#hired.alignment.finalize_report)(report)                           | Return a copy of `report` with every derivable field recomputed.                                                                        |
| [`is_blocking`](#hired.alignment.is_blocking)(record)                               | True for a gate-keeper requirement that is a hard gap or contradicted.                                                                  |
| [`render_report`](#hired.alignment.render_report)(report[, fmt])                      | Render `report` (a model or its JSON dict) in the named format.                                                                         |
| [`render_report_markdown`](#hired.alignment.render_report_markdown)(report)                    | Render the report as a Markdown string.                                                                                                 |
| [`render_report_html`](#hired.alignment.render_report_html)(report)                        | Render the report as a self-contained HTML page (inline CSS, no assets).                                                                |
| [`diff_reports`](#hired.alignment.diff_reports)(old, new)                            | Return a structured diff of two alignment-report dicts.                                                                                 |
| [`summarize_diff`](#hired.alignment.summarize_diff)(diff)                              | A short human-readable summary of [`diff_reports()`](#hired.alignment.diff_reports) output.                               |
| [`analyze_jd`](#hired.alignment.analyze_jd)(workspace, jd_text, \*, job_id[, ...]) | Analyse `jd_text` against the workspace candidate's facts and persist it.                                                               |
| [`aggregate_verdict`](#hired.alignment.aggregate_verdict)(records, \*[, apply_at, ...])   | The verdict and fit band, computed from classified records alone.                                                                       |
| [`coverage`](#hired.alignment.coverage)(records, \*[, class_weights, ...])       | `(coverage, resolved_share)`: weighted bucket credit over resolved records, and the weighted share of records that are resolved at all. |
| [`retrieve_facts`](#hired.alignment.retrieve_facts)(requirement, facts, \*[, k])       | The `k` facts sharing the most words with the requirement (none if none do).                                                            |
| [`quote_is_grounded`](#hired.alignment.quote_is_grounded)(quote, fact, \*[, min_words])   | True when `quote` is a verbatim span (modulo case/whitespace) of `fact`, at least `min_words` long.                                     |

### Classes

| [`Requirement`](#hired.alignment.Requirement)(\*[, id, skill_type, ...])             | One atomic requirement extracted verbatim from a job description.             |
|-----------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------|
| [`RequirementRecord`](#hired.alignment.RequirementRecord)(\*, requirement[, ...])          | The analysis of one requirement against the candidate's knowledge.            |
| [`Evidence`](#hired.alignment.Evidence)(\*, quote[, source_document_id, locator]) | A verbatim grounding span for a match judgment.                               |
| [`AlignmentReport`](#hired.alignment.AlignmentReport)(\*, job_id[, job_title, ...])      | A complete, verdict-first alignment analysis for one JD.                      |
| [`Verdict`](#hired.alignment.Verdict)(\*, recommendation[, confidence, ...])     |                                                                               |
| [`ScoreSummary`](#hired.alignment.ScoreSummary)(\*[, fit_band, bucket_counts, ...])   |                                                                               |
| [`NextAction`](#hired.alignment.NextAction)(\*, action[, addresses, priority, ...]) |                                                                               |
| [`Clarification`](#hired.alignment.Clarification)(\*, requirement_id, question[, ...]) | A question to ask the candidate to resolve a decision-relevant unknown.       |
| [`InterviewPrep`](#hired.alignment.InterviewPrep)(\*[, summary, talking_points, ...])  |                                                                               |
| [`Bucket`](#hired.alignment.Bucket)(\*values)                                   | The four alignment buckets.                                                   |
| [`MatchType`](#hired.alignment.MatchType)(\*values)                                | How the candidate's background relates to the requirement (Axis A).           |
| [`RequirementClass`](#hired.alignment.RequirementClass)(\*values)                         | How decision-critical a requirement is.                                       |
| [`SkillType`](#hired.alignment.SkillType)(\*values)                                |                                                                               |
| [`Closeability`](#hired.alignment.Closeability)(\*values)                             | How hard a gap is to close (Axis B), after the AI-leverage modifier.          |
| [`CloseMethod`](#hired.alignment.CloseMethod)(\*values)                              |                                                                               |
| [`TimeToClose`](#hired.alignment.TimeToClose)(\*values)                              |                                                                               |
| [`Transferability`](#hired.alignment.Transferability)(\*values)                          |                                                                               |
| [`AILeverage`](#hired.alignment.AILeverage)(\*values)                               | How much the candidate's standing AI-agent capability lowers the ramp.        |
| [`FieldCompleteness`](#hired.alignment.FieldCompleteness)(\*values)                        | Local closed-world flag: may a missing value be read as a real negative?      |
| [`Recommendation`](#hired.alignment.Recommendation)(\*values)                           |                                                                               |
| [`FitBand`](#hired.alignment.FitBand)(\*values)                                  |                                                                               |
| [`Consistency`](#hired.alignment.Consistency)(majority, agreement, entropy, ...)     | How far several sampled answers to one question agree.                        |
| [`MatchCalibrator`](#hired.alignment.MatchCalibrator)(match_threshold, ...[, ...])       | A fitted class-conditional conformal rule over a match score `s` in `[0, 1]`. |
| [`Decision`](#hired.alignment.Decision)(\*values)                                 | What to do with a judgment: take it as a match, as no match, or ask.          |
| [`LLMAlignmentAnalyzer`](#hired.alignment.LLMAlignmentAnalyzer)(\*[, model, client, ...])     | Draft an alignment report from JD text and facts, with an injected LLM.       |

### *class* hired.alignment.AILeverage(\*values)

Bases: [`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Enum`](https://docs.python.org/3/library/enum.html#enum.Enum)

How much the candidate’s standing AI-agent capability lowers the ramp.

Applies to *codified / knowledge-breadth* gaps, not tacit-judgment or
enduring-aptitude gaps (those it cannot rescue).

### *class* hired.alignment.AlignmentReport(\*, job_id, job_title='', company='', created_at='', verdict, score_summary=<factory>, requirements=<factory>, blocking_gaps=<factory>, next_actions=<factory>, interview_prep=<factory>, clarifications=<factory>)

Bases: `BaseModel`

A complete, verdict-first alignment analysis for one JD.

#### model_config *: [ClassVar](https://docs.python.org/3/library/typing.html#typing.ClassVar)[ConfigDict]* *= {}*

Configuration for the model, should be a dictionary conforming to [`ConfigDict`][pydantic.config.ConfigDict].

### *class* hired.alignment.Bucket(\*values)

Bases: [`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Enum`](https://docs.python.org/3/library/enum.html#enum.Enum)

The four alignment buckets.

### *class* hired.alignment.Clarification(, requirement_id, question, fills_field='', reason='', info_gain=0.0)

Bases: `BaseModel`

A question to ask the candidate to resolve a decision-relevant unknown.

#### model_config *: [ClassVar](https://docs.python.org/3/library/typing.html#typing.ClassVar)[ConfigDict]* *= {}*

Configuration for the model, should be a dictionary conforming to [`ConfigDict`][pydantic.config.ConfigDict].

### *class* hired.alignment.CloseMethod(\*values)

Bases: [`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Enum`](https://docs.python.org/3/library/enum.html#enum.Enum)

### *class* hired.alignment.Closeability(\*values)

Bases: [`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Enum`](https://docs.python.org/3/library/enum.html#enum.Enum)

How hard a gap is to close (Axis B), after the AI-leverage modifier.

### *class* hired.alignment.Consistency(majority, agreement, entropy, n_samples, counts=dict())

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

How far several sampled answers to one question agree.

`majority` is the most common meaning (`None` without samples),
`agreement` its share, `entropy` the Shannon entropy of the meanings
normalised to `[0, 1]` (0: all agree; 1: spread evenly over the meanings found), `counts` the
number of samples per meaning.

### *class* hired.alignment.Decision(\*values)

Bases: [`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Enum`](https://docs.python.org/3/library/enum.html#enum.Enum)

What to do with a judgment: take it as a match, as no match, or ask.

### *class* hired.alignment.Evidence(, quote, source_document_id='', locator='')

Bases: `BaseModel`

A verbatim grounding span for a match judgment.

#### model_config *: [ClassVar](https://docs.python.org/3/library/typing.html#typing.ClassVar)[ConfigDict]* *= {}*

Configuration for the model, should be a dictionary conforming to [`ConfigDict`][pydantic.config.ConfigDict].

### *class* hired.alignment.FieldCompleteness(\*values)

Bases: [`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Enum`](https://docs.python.org/3/library/enum.html#enum.Enum)

Local closed-world flag: may a missing value be read as a real negative?

### *class* hired.alignment.FitBand(\*values)

Bases: [`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Enum`](https://docs.python.org/3/library/enum.html#enum.Enum)

### *class* hired.alignment.InterviewPrep(\*, summary='', talking_points=<factory>, story_library=<factory>, proactive_disclosure='')

Bases: `BaseModel`

#### model_config *: [ClassVar](https://docs.python.org/3/library/typing.html#typing.ClassVar)[ConfigDict]* *= {}*

Configuration for the model, should be a dictionary conforming to [`ConfigDict`][pydantic.config.ConfigDict].

### *class* hired.alignment.LLMAlignmentAnalyzer(\*, model='gpt-4o-mini', client=None, api_key=None, n_samples=1, temperature=None, calibrator=None, retrieve=<function retrieve_facts>, top_k=5, nli=False, entails=None)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Draft an alignment report from JD text and facts, with an injected LLM.

`n_samples` > 1 judges each requirement several times and feeds the
agreement into [`apply_calibration()`](hired.alignment.calibration.html.md#hired.alignment.calibration.apply_calibration) (with
`calibrator`, the conformal ask/auto-decide rule). `nli` adds an
entailment check on every confirmed quote; `entails` replaces the default
(an LLM call) with any `(premise, hypothesis) -> bool`. `retrieve`
replaces the lexical [`retrieve_facts()`](#hired.alignment.retrieve_facts).

```pycon
>>> class _Fake:
...     class chat:
...         class completions:
...             @staticmethod
...             def create(**_): ...
>>> LLMAlignmentAnalyzer(client=_Fake()).analyze(jd_text, facts)
```

#### analyze(jd_text, facts, , job_id='job', job_title='', company='', requirements=None)

A draft report: decompose (unless `requirements` given), judge, aggregate.

* **Return type:**
  [`AlignmentReport`](hired.alignment.base.html.md#hired.alignment.base.AlignmentReport)

#### decompose(jd_text)

The JD’s atomic requirements, as the LLM extracts them.

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`Requirement`](hired.alignment.base.html.md#hired.alignment.base.Requirement)]

#### judge(requirement, facts)

One gated, optionally sampled-and-calibrated record for `requirement`.

* **Return type:**
  [`RequirementRecord`](hired.alignment.base.html.md#hired.alignment.base.RequirementRecord)

#### llm_entails(premise, hypothesis)

The LLM’s yes/no on whether `premise` establishes `hypothesis`.

* **Return type:**
  [`bool`](https://docs.python.org/3/builtins/functions.html#bool)

### *class* hired.alignment.MatchCalibrator(match_threshold, no_match_threshold, false_accept_rate=0.05, miss_rate=0.1, n_match=0, n_no_match=0)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

A fitted class-conditional conformal rule over a match score `s` in `[0, 1]`.

“Match” stays in the prediction set while its nonconformity `1 - s` is at most
`match_threshold`; “no match” while `s` is at most `no_match_threshold`.
A singleton set decides; two labels (or none) mean ask. JSON-ready through
[`to_dict()`](#hired.alignment.MatchCalibrator.to_dict) / [`from_dict()`](#hired.alignment.MatchCalibrator.from_dict), so a fitted rule can be stored and reviewed.

#### decide(score)

Auto-decide on a singleton prediction set; otherwise ask.

* **Return type:**
  [`Decision`](hired.alignment.base.html.md#hired.alignment.base.Decision)

#### *classmethod* from_dict(d)

Inverse of [`to_dict()`](#hired.alignment.MatchCalibrator.to_dict).

* **Return type:**
  [`MatchCalibrator`](hired.alignment.calibration.html.md#hired.alignment.calibration.MatchCalibrator)

#### prediction_set(score)

The labels (`True`: match) not excluded at their levels.

* **Return type:**
  [`frozenset`](https://docs.python.org/3/builtins/stdtypes.html#frozenset)[[`bool`](https://docs.python.org/3/builtins/functions.html#bool)]

#### to_dict()

A JSON-ready dict (an infinite threshold is written as `None`).

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]

### *class* hired.alignment.MatchType(\*values)

Bases: [`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Enum`](https://docs.python.org/3/library/enum.html#enum.Enum)

How the candidate’s background relates to the requirement (Axis A).

### *class* hired.alignment.NextAction(, action, addresses='', priority=1, expected_effect='')

Bases: `BaseModel`

#### model_config *: [ClassVar](https://docs.python.org/3/library/typing.html#typing.ClassVar)[ConfigDict]* *= {}*

Configuration for the model, should be a dictionary conforming to [`ConfigDict`][pydantic.config.ConfigDict].

### *class* hired.alignment.Recommendation(\*values)

Bases: [`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Enum`](https://docs.python.org/3/library/enum.html#enum.Enum)

### *class* hired.alignment.Requirement(\*, id=<factory>, text, skill_type=SkillType.TECHNICAL, requirement_class=RequirementClass.DIFFERENTIATOR, required_level=3)

Bases: `BaseModel`

One atomic requirement extracted verbatim from a job description.

#### model_config *: [ClassVar](https://docs.python.org/3/library/typing.html#typing.ClassVar)[ConfigDict]* *= {}*

Configuration for the model, should be a dictionary conforming to [`ConfigDict`][pydantic.config.ConfigDict].

### *class* hired.alignment.RequirementClass(\*values)

Bases: [`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Enum`](https://docs.python.org/3/library/enum.html#enum.Enum)

How decision-critical a requirement is.

### *class* hired.alignment.RequirementRecord(, requirement, match_state=MatchState.UNKNOWN, field_completeness=FieldCompleteness.OPEN, bucket=None, match_type=MatchType.NONE, candidate_level=0, gap_size=0, source_skill=None, adjacency_basis=None, transferability=None, closeability=None, close_method=None, time_to_close=None, ai_leverage=AILeverage.NONE, confidence=ConfidenceLevel.LOW, uncertainty_reason=None, evidence=None, match_score=None, calibrated_decision=None, impact=3, info_gain=0.0, needs_clarification=False, talking_point=None)

Bases: `BaseModel`

The analysis of one requirement against the candidate’s knowledge.

#### model_config *: [ClassVar](https://docs.python.org/3/library/typing.html#typing.ClassVar)[ConfigDict]* *= {}*

Configuration for the model, should be a dictionary conforming to [`ConfigDict`][pydantic.config.ConfigDict].

### *class* hired.alignment.ScoreSummary(\*, fit_band=FitBand.FAIR, bucket_counts=<factory>, ats_readability=None)

Bases: `BaseModel`

#### model_config *: [ClassVar](https://docs.python.org/3/library/typing.html#typing.ClassVar)[ConfigDict]* *= {}*

Configuration for the model, should be a dictionary conforming to [`ConfigDict`][pydantic.config.ConfigDict].

### *class* hired.alignment.SkillType(\*values)

Bases: [`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Enum`](https://docs.python.org/3/library/enum.html#enum.Enum)

### *class* hired.alignment.TimeToClose(\*values)

Bases: [`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Enum`](https://docs.python.org/3/library/enum.html#enum.Enum)

### *class* hired.alignment.Transferability(\*values)

Bases: [`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Enum`](https://docs.python.org/3/library/enum.html#enum.Enum)

### *class* hired.alignment.Verdict(\*, recommendation, confidence=ConfidenceLevel.MEDIUM, confidence_basis='', headline='', key_reasons=<factory>, has_blocking_gaps=False)

Bases: `BaseModel`

#### model_config *: [ClassVar](https://docs.python.org/3/library/typing.html#typing.ClassVar)[ConfigDict]* *= {}*

Configuration for the model, should be a dictionary conforming to [`ConfigDict`][pydantic.config.ConfigDict].

### hired.alignment.aggregate_verdict(records, , apply_at=0.7, stretch_at=0.4, fit_bands=((0.85, FitBand.GREAT), (0.7, FitBand.GOOD), (0.5, FitBand.FAIR), (0.3, FitBand.WEAK), (0.0, FitBand.POOR)), class_weights={RequirementClass.DIFFERENTIATOR: 2.0, RequirementClass.GATE_KEEPER: 3.0, RequirementClass.VALUE_ADD: 1.0}, bucket_credit={Bucket.ADJACENT_TRANSFERABLE: 0.5, Bucket.GAP_HARD: 0.0, Bucket.GAP_LEARNABLE: 0.25, Bucket.STRONG_MATCH: 1.0})

The verdict and fit band, computed from classified records alone.

A blocking gap (a gate-keeper that is a hard gap or contradicted) means
*do not apply*; otherwise the weighted coverage picks the recommendation.
Confidence comes from how much of the JD is resolved, not from the LLM.

```pycon
>>> from hired.alignment.base import MatchType
>>> rec = classify(RequirementRecord(requirement=Requirement(text='Python'),
...     match_state='confirmed', match_type=MatchType.DIRECT, candidate_level=4))
>>> verdict, band = aggregate_verdict([rec])
>>> verdict.recommendation.value, band.value, verdict.confidence.value
('apply', 'great', 'high')
```

* **Return type:**
  [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`Verdict`](hired.alignment.base.html.md#hired.alignment.base.Verdict), [`FitBand`](hired.alignment.base.html.md#hired.alignment.base.FitBand)]

### hired.alignment.analyze_jd(workspace, jd_text, , job_id, job_title='', analyzer=None, requirements=None)

Analyse `jd_text` against the workspace candidate’s facts and persist it.

The draft goes through `JDWorkspace.save_alignment()` (finalize + archive +
save), the one path from a draft to a stored report. `analyzer` defaults to
an [`LLMAlignmentAnalyzer`](#hired.alignment.LLMAlignmentAnalyzer) on the `ai` extra.

* **Return type:**
  [`AlignmentReport`](hired.alignment.base.html.md#hired.alignment.base.AlignmentReport)

### hired.alignment.apply_ai_leverage(closeability, ai_leverage, , skill_type, is_tacit=False)

Soften a *codified* gap’s closeability by the candidate’s AI leverage.

Tacit/soft gaps and structurally-hard gaps are never softened — AI agents
extend *breadth of codified knowledge*, not judgment or enduring aptitude.

```pycon
>>> apply_ai_leverage(Closeability.REQUIRES_EXPERIENCE, AILeverage.HIGH,
...                    skill_type=SkillType.TECHNICAL)
<Closeability.LEARNABLE: 'learnable'>
>>> apply_ai_leverage(Closeability.REQUIRES_EXPERIENCE, AILeverage.HIGH,
...                    skill_type=SkillType.SOFT_SKILL)
<Closeability.REQUIRES_EXPERIENCE: 'requires_experience'>
```

* **Return type:**
  [`Closeability`](hired.alignment.base.html.md#hired.alignment.base.Closeability)

### hired.alignment.apply_calibration(record, samples, , calibrator=None, meaning=None, is_match=None)

Set `record`’s confidence from sampled judgments, and its decision if calibrated.

`samples` are several independent judgments of the same requirement (match
states, by default). The record’s `confidence` becomes
[`confidence_level()`](#hired.alignment.confidence_level) of their agreement and its `match_score`
[`match_share()`](#hired.alignment.match_share); with a `calibrator`, `calibrated_decision` is its
[`decide()`](#hired.alignment.MatchCalibrator.decide), which [`should_ask()`](hired.alignment.elicitation.html.md#hired.alignment.elicitation.should_ask)
honours (without one it is cleared: new samples supersede an old decision, so
re-apply, or clear it, once an answer settles the requirement). The match state stays the analyst’s: an *ask* questions a claim, it
does not overturn it. Returns the record, changed in place.

```pycon
>>> from hired.alignment.base import Requirement
>>> rec = RequirementRecord(requirement=Requirement(text="Kafka"), match_state="confirmed")
>>> rec = apply_calibration(rec, ["confirmed", "confirmed", "unknown"])
>>> rec.confidence.value, round(rec.match_score, 2), rec.calibrated_decision
('medium', 0.67, None)
```

* **Return type:**
  [`RequirementRecord`](hired.alignment.base.html.md#hired.alignment.base.RequirementRecord)

### hired.alignment.assign_bucket(record)

Assign the alignment bucket for a record, or `None` if it should be a
clarifying question instead.

Returns `None` when the requirement is `UNKNOWN` on an OPEN field — that
routes to elicitation rather than being scored as a gap (the “don’t assume
absence” rule). `UNKNOWN` on a CLOSED field is treated as a real gap.

* **Return type:**
  [`Bucket`](hired.alignment.base.html.md#hired.alignment.base.Bucket) | [`None`](https://docs.python.org/3/builtins/constants.html#None)

### hired.alignment.calibrate_match(scores, labels, , false_accept_rate=0.05, miss_rate=0.1)

Fit the ask/auto-decide rule on held-out judgments with known truth.

`scores` are match scores in `[0, 1]` (say [`match_share()`](#hired.alignment.match_share) of sampled
judgments), `labels` whether each was truly a match. Each class gets its own
threshold (Mondrian split conformal): `false_accept_rate` bounds how often a
true non-match is auto-accepted, `miss_rate` how often a true match is
auto-rejected. Keep the held-out set apart from anything used to tune the
scoring, or the bound does not hold.

* **Return type:**
  [`MatchCalibrator`](hired.alignment.calibration.html.md#hired.alignment.calibration.MatchCalibrator)

### hired.alignment.classify(record)

Fill `gap_size` and `bucket` (and `needs_clarification`) in place.

Returns the same record for convenience.

* **Return type:**
  [`RequirementRecord`](hired.alignment.base.html.md#hired.alignment.base.RequirementRecord)

### hired.alignment.compute_gap_size(required_level, candidate_level)

Residual gap, floored at zero.

* **Return type:**
  [`int`](https://docs.python.org/3/builtins/functions.html#int)

### hired.alignment.confidence_level(agreement, , high=0.9, medium=0.6)

A `ConfidenceLevel` from sampled agreement rather than self-report.

```pycon
>>> confidence_level(0.95), confidence_level(0.7), confidence_level(0.5)
(<ConfidenceLevel.HIGH: 'high'>, <ConfidenceLevel.MEDIUM: 'medium'>, <ConfidenceLevel.LOW: 'low'>)
```

* **Return type:**
  [`ConfidenceLevel`](hired.candidate.base.html.md#hired.candidate.base.ConfidenceLevel)

### hired.alignment.coverage(records, , class_weights={RequirementClass.DIFFERENTIATOR: 2.0, RequirementClass.GATE_KEEPER: 3.0, RequirementClass.VALUE_ADD: 1.0}, bucket_credit={Bucket.ADJACENT_TRANSFERABLE: 0.5, Bucket.GAP_HARD: 0.0, Bucket.GAP_LEARNABLE: 0.25, Bucket.STRONG_MATCH: 1.0})

`(coverage, resolved_share)`: weighted bucket credit over resolved records,
and the weighted share of records that are resolved at all.

Records must be classified (see [`classify()`](hired.alignment.rubric.html.md#hired.alignment.rubric.classify)).

* **Return type:**
  [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`float`](https://docs.python.org/3/builtins/functions.html#float), [`float`](https://docs.python.org/3/builtins/functions.html#float)]

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

### hired.alignment.finalize_report(report)

Return a copy of `report` with every derivable field recomputed.

Clarifications and flagged blockers refer to requirements by `id`; give
requirements explicit ids in a draft so those links survive (flagged
blockers also fall back to matching by requirement text).

```pycon
>>> from hired.alignment import (AlignmentReport, Requirement, RequirementRecord,
...     RequirementClass, Verdict, Recommendation, MatchType, Closeability)
>>> from hired.candidate.base import MatchState
>>> gate = Requirement(id='r1', text='PhD', requirement_class=RequirementClass.GATE_KEEPER)
>>> recs = [
...     RequirementRecord(requirement=gate, closeability=Closeability.STRUCTURALLY_HARD,
...                       match_state=MatchState.CONTRADICTED),
...     RequirementRecord(requirement=Requirement(id='r2', text='Python', required_level=3),
...                       match_state=MatchState.CONFIRMED, match_type=MatchType.DIRECT,
...                       candidate_level=5),
... ]
>>> report = finalize_report(AlignmentReport(
...     job_id='ds', verdict=Verdict(recommendation=Recommendation.STRETCH),
...     requirements=recs))
>>> report.score_summary.bucket_counts['strong_match']
1
>>> [r.requirement.id for r in report.blocking_gaps], report.verdict.has_blocking_gaps
(['r1'], True)
```

* **Return type:**
  [`AlignmentReport`](hired.alignment.base.html.md#hired.alignment.base.AlignmentReport)

### hired.alignment.info_gain(record)

Expected information gain of resolving this requirement, wrt the verdict.

Heuristic: `uncertainty × criticality`. An `impact` override (1-5) scales
criticality when the analyst has a sharper view than the requirement class.

* **Return type:**
  [`float`](https://docs.python.org/3/builtins/functions.html#float)

### hired.alignment.is_blocking(record)

True for a gate-keeper requirement that is a hard gap or contradicted.

* **Return type:**
  [`bool`](https://docs.python.org/3/builtins/functions.html#bool)

### hired.alignment.is_decision_stable(records)

True when no remaining open unknown could flip the verdict.

Concretely: there are no askable (decision-relevant, open, unknown)
requirements left. This is the sharpest stop criterion from the research.

* **Return type:**
  [`bool`](https://docs.python.org/3/builtins/functions.html#bool)

### hired.alignment.match_share(samples, , is_match=None)

The share of sampled judgments that say “match”: a score in `[0, 1]`.

By default a sample matches when it is (or names) `MatchState.CONFIRMED`;
`is_match` overrides that. This is the score [`calibrate_match()`](#hired.alignment.calibrate_match) takes.

```pycon
>>> match_share(["confirmed", "confirmed", "unknown", "contradicted"])
0.5
```

* **Return type:**
  [`float`](https://docs.python.org/3/builtins/functions.html#float)

### hired.alignment.quote_is_grounded(quote, fact, , min_words=2)

True when `quote` is a verbatim span (modulo case/whitespace) of `fact`,
at least `min_words` long.

```pycon
>>> quote_is_grounded('kafka  CLUSTERS', Fact(statement='Ran Kafka clusters'))
True
>>> quote_is_grounded('Kafka expert', Fact(statement='Ran Kafka clusters'))
False
>>> quote_is_grounded('Kafka', Fact(statement='Ran Kafka clusters'))
False
```

* **Return type:**
  [`bool`](https://docs.python.org/3/builtins/functions.html#bool)

### hired.alignment.rank_clarifications(records, , max_questions=None, min_info_gain=0.0)

Produce clarifying questions for askable records, highest info-gain first.

The question *text* is left to the analyst; this returns the prioritized
skeleton (requirement, reason, info_gain) so the caller can fill `question`.

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`Clarification`](hired.alignment.base.html.md#hired.alignment.base.Clarification)]

### hired.alignment.render_report(report, fmt='markdown')

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

### hired.alignment.render_report_html(report)

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

### hired.alignment.render_report_markdown(report)

Render the report as a Markdown string.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### hired.alignment.retrieve_facts(requirement, facts, , k=5)

The `k` facts sharing the most words with the requirement (none if none do).

Lexical, so it misses an adjacent skill named in different words (RabbitMQ
for Kafka); inject a semantic `retrieve` into the analyzer for that.

```pycon
>>> from hired.candidate.base import Fact
>>> fs = [Fact(statement='Ran Kafka clusters'), Fact(statement='Speaks French')]
>>> [f.statement for f in retrieve_facts(Requirement(text='Kafka streaming'), fs)]
['Ran Kafka clusters']
```

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`Fact`](hired.candidate.base.html.md#hired.candidate.base.Fact)]

### hired.alignment.semantic_consistency(samples, , meaning=None)

The agreement of sampled answers, clustered by `meaning` (default: equality).

`meaning` maps an answer to its meaning: a normalised label, an entailment
cluster id. Answers that mean the same count as agreeing however worded.

```pycon
>>> c = semantic_consistency(["Yes", "yes", "no", "YES "], meaning=lambda s: s.strip().lower())
>>> c.majority, c.agreement, round(c.entropy, 3)
('yes', 0.75, 0.811)
>>> semantic_consistency([]).agreement
0.0
```

* **Return type:**
  [`Consistency`](hired.alignment.calibration.html.md#hired.alignment.calibration.Consistency)

### hired.alignment.should_ask(record)

Whether to route this record to a clarifying question.

Ask only when it’s `UNKNOWN` on an OPEN field and decision-relevant — the
“don’t assume absence from silence” rule. CONTRADICTED facts and closed-field
unknowns are real gaps, not questions. A decision-relevant CONFIRMED or
CONTRADICTED record whose calibrated decision is *ask* (sampled judgments too
inconsistent for the conformal rule, see [`hired.alignment.calibration`](hired.alignment.calibration.html.md#module-hired.alignment.calibration))
is asked about too: “never exaggerate” means a shaky match is confirmed first,
and a shaky absence is not assumed. An UNKNOWN follows the rule above.

* **Return type:**
  [`bool`](https://docs.python.org/3/builtins/functions.html#bool)

### hired.alignment.summarize_diff(diff)

A short human-readable summary of [`diff_reports()`](#hired.alignment.diff_reports) output.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### Modules

| [`analyzer`](hired.alignment.analyzer.html.md#module-hired.alignment.analyzer)               | Library-mode autonomous alignment analysis, driven by an injected LLM.                                                               |
|---------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------|
| [`assemble`](hired.alignment.assemble.html.md#module-hired.alignment.assemble)               | Deterministically finalize an analyst-drafted [`AlignmentReport`](#hired.alignment.AlignmentReport).                      |
| [`base`](hired.alignment.base.html.md#module-hired.alignment.base)                       | Schemas for JD-vs-candidate alignment analysis.                                                                                      |
| [`calibration`](hired.alignment.calibration.html.md#module-hired.alignment.calibration)         | Calibrated confidence: multi-sample consistency and a conformal ask/auto-decide rule.                                                |
| [`calibration_log`](hired.alignment.calibration_log.html.md#module-hired.alignment.calibration_log) | Collect held-out (score, truth) pairs from answered clarifications and fit a calibrator.                                             |
| [`diff`](hired.alignment.diff.html.md#module-hired.alignment.diff)                       | Deterministic diff between two alignment reports.                                                                                    |
| [`elicitation`](hired.alignment.elicitation.html.md#module-hired.alignment.elicitation)         | The honesty loop: rank unknowns into the most informative questions first.                                                           |
| [`report`](hired.alignment.report.html.md#module-hired.alignment.report)                   | Render an [`AlignmentReport`](hired.alignment.base.html.md#hired.alignment.base.AlignmentReport) to Markdown or HTML. |
| [`rubric`](hired.alignment.rubric.html.md#module-hired.alignment.rubric)                   | Deterministic bucket assignment — the two-axis rubric in code.                                                                       |
