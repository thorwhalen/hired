# hired.alignment.elicitation

The honesty loop: rank unknowns into the most informative questions first.

This module is deterministic scaffolding around a judgment the analyst makes.
It computes which `UNKNOWN` requirements are worth asking about, in what order
(by expected information gain ≈ profile-uncertainty × requirement-criticality),
and whether the analysis has become *decision-stable* enough to stop.

See `misc/docs/DESIGN.md` §8.

### Functions

| [`info_gain`](#hired.alignment.elicitation.info_gain)(record)                       | Expected information gain of resolving this requirement, wrt the verdict.                                                                   |
|------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------|
| [`is_decision_relevant`](#hired.alignment.elicitation.is_decision_relevant)(record)            | A requirement is worth asking about only if resolving it could move the verdict — i.e. it's not a low-value-add nice-to-have we can ignore. |
| [`is_decision_stable`](#hired.alignment.elicitation.is_decision_stable)(records)             | True when no remaining open unknown could flip the verdict.                                                                                 |
| [`rank_clarifications`](#hired.alignment.elicitation.rank_clarifications)(records, \*[, ...]) | Produce clarifying questions for askable records, highest info-gain first.                                                                  |
| [`should_ask`](#hired.alignment.elicitation.should_ask)(record)                      | Whether to route this record to a clarifying question.                                                                                      |

### hired.alignment.elicitation.info_gain(record)

Expected information gain of resolving this requirement, wrt the verdict.

Heuristic: `uncertainty × criticality`. An `impact` override (1-5) scales
criticality when the analyst has a sharper view than the requirement class.

* **Return type:**
  [`float`](https://docs.python.org/3/builtins/functions.html#float)

### hired.alignment.elicitation.is_decision_relevant(record)

A requirement is worth asking about only if resolving it could move the
verdict — i.e. it’s not a low-value-add nice-to-have we can ignore.

* **Return type:**
  [`bool`](https://docs.python.org/3/builtins/functions.html#bool)

### hired.alignment.elicitation.is_decision_stable(records)

True when no remaining open unknown could flip the verdict.

Concretely: there are no askable (decision-relevant, open, unknown)
requirements left. This is the sharpest stop criterion from the research.

* **Return type:**
  [`bool`](https://docs.python.org/3/builtins/functions.html#bool)

### hired.alignment.elicitation.rank_clarifications(records, , max_questions=None, min_info_gain=0.0)

Produce clarifying questions for askable records, highest info-gain first.

The question *text* is left to the analyst; this returns the prioritized
skeleton (requirement, reason, info_gain) so the caller can fill `question`.

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`Clarification`](hired.alignment.base.html.md#hired.alignment.base.Clarification)]

### hired.alignment.elicitation.should_ask(record)

Whether to route this record to a clarifying question.

Ask only when it’s `UNKNOWN` on an OPEN field and decision-relevant — the
“don’t assume absence from silence” rule. CONTRADICTED facts and closed-field
unknowns are real gaps, not questions.

* **Return type:**
  [`bool`](https://docs.python.org/3/builtins/functions.html#bool)
