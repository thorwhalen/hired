# hired.alignment.calibration_log

Collect held-out (score, truth) pairs from answered clarifications and fit a calibrator.

[`calibrate_match()`](hired.alignment.calibration.html.md#hired.alignment.calibration.calibrate_match) needs scored judgments with known
truth. The truth arrives when the candidate answers a clarifying question
([`record_qa()`](hired.candidate.html.md#hired.candidate.CandidateKnowledgeBase.record_qa)): the record’s `match_score`
*before* the answer, plus what the answer established. [`CalibrationLog`](#hired.alignment.calibration_log.CalibrationLog) appends
each pair to the user’s `info/calibration/pairs.jsonl` and, once both classes have enough
pairs for the chosen levels, fits and persists a `MatchCalibrator`
(`info/calibration/calibrator.json`) that the `hired-align` workflow loads with
[`CalibrationLog.load_calibrator()`](#hired.alignment.calibration_log.CalibrationLog.load_calibrator).

Keep these pairs out of anything used to tune the scoring: the conformal bound only holds
for data the scorer never saw.

```pycon
>>> import tempfile
>>> from hired.persistence.base import UserStore
>>> log = CalibrationLog(UserStore("t", root=tempfile.mkdtemp()))
>>> log.add(0.9, True, qa_id="qa-1")
>>> log.pairs()
[(0.9, True)]
>>> log.fit() is None  # too few pairs for the default levels
True
```

### Functions

| [`min_pairs`](#hired.alignment.calibration_log.min_pairs)(rate)   | Pairs a class needs for a finite threshold at `rate`: `ceil(1/rate) - 1`.   |
|--------------------------------------------------------------------|-----------------------------------------------------------------------------|

### Classes

| [`CalibrationLog`](#hired.alignment.calibration_log.CalibrationLog)([store, false_accept_rate, ...])   | The user's calibration pairs and fitted calibrator, kept under `info/calibration/`.   |
|----------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------|

### *class* hired.alignment.calibration_log.CalibrationLog(store=None, , false_accept_rate=0.05, miss_rate=0.1)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

The user’s calibration pairs and fitted calibrator, kept under `info/calibration/`.

#### add(match_score, truth, , qa_id=None)

Append one pair (the score before the answer, the truth the answer established).

* **Return type:**
  [`None`](https://docs.python.org/3/builtins/constants.html#None)

#### add_and_refit(match_score, truth, , qa_id=None)

[`add()`](#hired.alignment.calibration_log.CalibrationLog.add) a pair, then refit and persist when ready; return the calibrator.

* **Return type:**
  [`MatchCalibrator`](hired.alignment.calibration.html.md#hired.alignment.calibration.MatchCalibrator) | [`None`](https://docs.python.org/3/builtins/constants.html#None)

#### fit(, persist=False)

Fit on the logged pairs; `None` until [`ready()`](#hired.alignment.calibration_log.CalibrationLog.ready). `persist` saves the result.

* **Return type:**
  [`MatchCalibrator`](hired.alignment.calibration.html.md#hired.alignment.calibration.MatchCalibrator) | [`None`](https://docs.python.org/3/builtins/constants.html#None)

#### load_calibrator()

The persisted calibrator, or `None` if none has been fitted yet.

* **Return type:**
  [`MatchCalibrator`](hired.alignment.calibration.html.md#hired.alignment.calibration.MatchCalibrator) | [`None`](https://docs.python.org/3/builtins/constants.html#None)

#### ready()

Whether each class has enough pairs for its level.

* **Return type:**
  [`bool`](https://docs.python.org/3/builtins/functions.html#bool)

### hired.alignment.calibration_log.min_pairs(rate)

Pairs a class needs for a finite threshold at `rate`: `ceil(1/rate) - 1`.

```pycon
>>> min_pairs(0.05), min_pairs(0.1)
(19, 9)
```

* **Return type:**
  [`int`](https://docs.python.org/3/builtins/functions.html#int)
