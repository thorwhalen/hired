# hired.alignment.calibration

Calibrated confidence: multi-sample consistency and a conformal ask/auto-decide rule.

Self-reported confidence (an LLM saying “high”) is overconfident; the honesty
contract needs a signal that is not. Two deterministic pieces, the judgments
themselves staying external (the `hired-align` skill or an injected LLM):

1. **Consistency.** Ask the same question several times and see how often the
   answers agree in meaning ([`semantic_consistency()`](#hired.alignment.calibration.semantic_consistency)). Agreement is the
   signal; [`match_share()`](#hired.alignment.calibration.match_share) turns sampled match states into a score in
   `[0, 1]` and [`confidence_level()`](#hired.alignment.calibration.confidence_level) into a `ConfidenceLevel`.
2. **Conformal abstention.** On a held-out set of scored, labelled judgments,
   [`calibrate_match()`](#hired.alignment.calibration.calibrate_match) fits a class-conditional (Mondrian) split-conformal
   > rule. [`MatchCalibrator.decide()`](#hired.alignment.calibration.MatchCalibrator.decide) then auto-accepts a match only when the
   > score excludes “no match” at level `false_accept_rate`, auto-rejects only
   > when it excludes “match” at level `miss_rate`, and otherwise says *ask*.

The guarantee: over calibration and test drawn alike (exchangeable), a true
non-match is auto-accepted with probability at most `false_accept_rate`, and a
true match auto-rejected with probability at most `miss_rate`. The asymmetry
(“never exaggerate”) is the choice of a smaller `false_accept_rate`. With too
few calibration examples of a class to support its level, the rule never
auto-decides against that class: it asks.

See `misc/docs/research/jd-candidate-matching.md` (unknown vs absent) and #12.

```pycon
>>> scores = [0.9, 0.95, 0.8, 1.0, 0.85] * 8 + [0.1, 0.2, 0.0, 0.3, 0.15] * 8
>>> labels = [True] * 40 + [False] * 40
>>> cal = calibrate_match(scores, labels, false_accept_rate=0.05, miss_rate=0.1)
>>> cal.decide(0.97), cal.decide(0.05), cal.decide(0.5)
(<Decision.AUTO_MATCH: 'auto_match'>, <Decision.AUTO_NO_MATCH: 'auto_no_match'>, <Decision.ASK: 'ask'>)
```

### Functions

| [`calibrate_match`](#hired.alignment.calibration.calibrate_match)(scores, labels, \*[, ...])      | Fit the ask/auto-decide rule on held-out judgments with known truth.          |
|--------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------|
| [`conformal_quantile`](#hired.alignment.calibration.conformal_quantile)(scores, alpha)               | The split-conformal threshold: the `ceil((n+1)(1-alpha))`-th smallest score.  |
| [`confidence_level`](#hired.alignment.calibration.confidence_level)(agreement, \*[, high, medium]) | A `ConfidenceLevel` from sampled agreement rather than self-report.           |
| [`match_share`](#hired.alignment.calibration.match_share)(samples, \*[, is_match])            | The share of sampled judgments that say "match": a score in `[0, 1]`.         |
| [`semantic_consistency`](#hired.alignment.calibration.semantic_consistency)(samples, \*[, meaning])    | The agreement of sampled answers, clustered by `meaning` (default: equality). |

### Classes

| [`Consistency`](#hired.alignment.calibration.Consistency)(majority, agreement, entropy, ...)   | How far several sampled answers to one question agree.                        |
|---------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------|
| [`Decision`](#hired.alignment.calibration.Decision)(\*values)                               | What to do with a judgment: take it as a match, as no match, or ask.          |
| [`MatchCalibrator`](#hired.alignment.calibration.MatchCalibrator)(match_threshold, ...[, ...])     | A fitted class-conditional conformal rule over a match score `s` in `[0, 1]`. |

### *class* hired.alignment.calibration.Consistency(majority, agreement, entropy, n_samples, counts=dict())

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

How far several sampled answers to one question agree.

`majority` is the most common meaning (`None` without samples),
`agreement` its share, `entropy` the Shannon entropy of the meanings
normalised to `[0, 1]` (0: all agree; 1: all differ), `counts` the
number of samples per meaning.

### *class* hired.alignment.calibration.Decision(\*values)

Bases: [`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Enum`](https://docs.python.org/3/library/enum.html#enum.Enum)

What to do with a judgment: take it as a match, as no match, or ask.

### *class* hired.alignment.calibration.MatchCalibrator(match_threshold, no_match_threshold, false_accept_rate=0.05, miss_rate=0.1, n_match=0, n_no_match=0)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

A fitted class-conditional conformal rule over a match score `s` in `[0, 1]`.

“Match” stays in the prediction set while its nonconformity `1 - s` is at most
`match_threshold`; “no match” while `s` is at most `no_match_threshold`.
A singleton set decides; two labels (or none) mean ask. JSON-ready through
[`to_dict()`](#hired.alignment.calibration.MatchCalibrator.to_dict) / [`from_dict()`](#hired.alignment.calibration.MatchCalibrator.from_dict), so a fitted rule can be stored and reviewed.

#### decide(score)

Auto-decide on a singleton prediction set; otherwise ask.

* **Return type:**
  [`Decision`](#hired.alignment.calibration.Decision)

#### *classmethod* from_dict(d)

Inverse of [`to_dict()`](#hired.alignment.calibration.MatchCalibrator.to_dict).

* **Return type:**
  [`MatchCalibrator`](#hired.alignment.calibration.MatchCalibrator)

#### prediction_set(score)

The labels (`True`: match) not excluded at their levels.

* **Return type:**
  [`frozenset`](https://docs.python.org/3/builtins/stdtypes.html#frozenset)[[`bool`](https://docs.python.org/3/builtins/functions.html#bool)]

#### to_dict()

A JSON-ready dict (an infinite threshold is written as `None`).

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]

### hired.alignment.calibration.calibrate_match(scores, labels, , false_accept_rate=0.05, miss_rate=0.1)

Fit the ask/auto-decide rule on held-out judgments with known truth.

`scores` are match scores in `[0, 1]` (say [`match_share()`](#hired.alignment.calibration.match_share) of sampled
judgments), `labels` whether each was truly a match. Each class gets its own
threshold (Mondrian split conformal): `false_accept_rate` bounds how often a
true non-match is auto-accepted, `miss_rate` how often a true match is
auto-rejected. Keep the held-out set apart from anything used to tune the
scoring, or the bound does not hold.

* **Return type:**
  [`MatchCalibrator`](#hired.alignment.calibration.MatchCalibrator)

### hired.alignment.calibration.confidence_level(agreement, , high=0.9, medium=0.6)

A `ConfidenceLevel` from sampled agreement rather than self-report.

```pycon
>>> confidence_level(0.95), confidence_level(0.7), confidence_level(0.5)
(<ConfidenceLevel.HIGH: 'high'>, <ConfidenceLevel.MEDIUM: 'medium'>, <ConfidenceLevel.LOW: 'low'>)
```

* **Return type:**
  [`ConfidenceLevel`](hired.candidate.base.html.md#hired.candidate.base.ConfidenceLevel)

### hired.alignment.calibration.conformal_quantile(scores, alpha)

The split-conformal threshold: the `ceil((n+1)(1-alpha))`-th smallest score.

A new score drawn like these exceeds it with probability at most `alpha`.
When `n` is too small for `alpha` (`ceil((n+1)(1-alpha)) > n`) no finite
threshold has that guarantee, and this returns `inf`.

```pycon
>>> conformal_quantile([0.1, 0.2, 0.3, 0.4], 0.2)  # ceil(5 * 0.8) = 4th
0.4
>>> conformal_quantile([0.1, 0.2], 0.1)
inf
```

* **Return type:**
  [`float`](https://docs.python.org/3/builtins/functions.html#float)

### hired.alignment.calibration.match_share(samples, , is_match=None)

The share of sampled judgments that say “match”: a score in `[0, 1]`.

By default a sample matches when it is (or names) `MatchState.CONFIRMED`;
`is_match` overrides that. This is the score [`calibrate_match()`](#hired.alignment.calibration.calibrate_match) takes.

```pycon
>>> match_share(["confirmed", "confirmed", "unknown", "contradicted"])
0.5
```

* **Return type:**
  [`float`](https://docs.python.org/3/builtins/functions.html#float)

### hired.alignment.calibration.semantic_consistency(samples, , meaning=None)

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
  [`Consistency`](#hired.alignment.calibration.Consistency)
