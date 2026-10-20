"""Calibrated confidence (#12): consistency signals and conformal ask/auto-decide.

All data synthetic: scores drawn from known distributions, no candidate data.
"""

import json
import math
import random

import pytest

from hired.alignment.calibration import (
    Decision,
    MatchCalibrator,
    calibrate_match,
    conformal_quantile,
    confidence_level,
    match_share,
    semantic_consistency,
)
from hired.candidate.base import ConfidenceLevel, MatchState


def _draw(rng, n, *, match):
    """Match scores: true matches mostly high, non-matches mostly low, overlapping."""
    mu = 0.75 if match else 0.3
    return [min(max(rng.gauss(mu, 0.2), 0.0), 1.0) for _ in range(n)]


def test_false_accepts_stay_within_the_stated_rate():
    """Across many calibration/test draws, the auto-accept rate on true non-matches
    averages at most false_accept_rate (the marginal conformal guarantee)."""
    rng = random.Random(0)
    alpha, rates = 0.05, []
    for _ in range(200):
        cal = calibrate_match(
            _draw(rng, 60, match=True) + _draw(rng, 60, match=False),
            [True] * 60 + [False] * 60,
            false_accept_rate=alpha,
            miss_rate=0.2,
        )
        test = _draw(rng, 50, match=False)
        rates.append(sum(cal.decide(s) is Decision.AUTO_MATCH for s in test) / len(test))
    assert sum(rates) / len(rates) <= alpha + 0.01


def test_misses_stay_within_the_stated_rate():
    rng = random.Random(1)
    beta, rates = 0.1, []
    for _ in range(200):
        cal = calibrate_match(
            _draw(rng, 60, match=True) + _draw(rng, 60, match=False),
            [True] * 60 + [False] * 60,
            miss_rate=beta,
        )
        test = _draw(rng, 50, match=True)
        rates.append(sum(cal.decide(s) is Decision.AUTO_NO_MATCH for s in test) / len(test))
    assert sum(rates) / len(rates) <= beta + 0.01


def test_a_tighter_false_accept_rate_asks_more():
    rng = random.Random(2)
    scores = _draw(rng, 100, match=True) + _draw(rng, 100, match=False)
    labels = [True] * 100 + [False] * 100
    loose = calibrate_match(scores, labels, false_accept_rate=0.2)
    tight = calibrate_match(scores, labels, false_accept_rate=0.02)
    probe = [i / 100 for i in range(101)]
    auto = lambda cal: sum(cal.decide(s) is Decision.AUTO_MATCH for s in probe)  # noqa: E731
    assert auto(tight) < auto(loose)


def test_too_few_examples_of_a_class_never_decides_against_it():
    cal = calibrate_match([0.9, 0.1, 0.2], [True, False, False], false_accept_rate=0.05)
    assert math.isinf(cal.no_match_threshold)  # 2 non-matches cannot support 5%
    assert cal.decide(1.0) is Decision.ASK  # so a match is never auto-accepted
    assert calibrate_match([], []).decide(0.5) is Decision.ASK


def test_round_trips_through_json():
    cal = calibrate_match([0.9] * 30 + [0.1, 0.2], [True] * 30 + [False] * 2)
    back = MatchCalibrator.from_dict(json.loads(json.dumps(cal.to_dict())))
    assert back == cal


@pytest.mark.parametrize("bad", [-0.1, 1.5, math.nan])
def test_scores_outside_the_unit_interval_are_errors(bad):
    with pytest.raises(ValueError, match="match score"):
        calibrate_match([bad], [True])


def test_mismatched_scores_and_labels_are_errors():
    with pytest.raises(ValueError):
        calibrate_match([0.5, 0.6], [True])


def test_conformal_quantile_guards_alpha():
    with pytest.raises(ValueError, match="alpha"):
        conformal_quantile([0.1], 0.0)


def test_consistency_feeds_confidence_and_match_share():
    samples = [MatchState.CONFIRMED] * 9 + [MatchState.UNKNOWN]
    c = semantic_consistency(samples)
    assert c.majority is MatchState.CONFIRMED and c.agreement == 0.9
    assert confidence_level(c) is ConfidenceLevel.HIGH
    assert match_share(samples) == 0.9
    assert semantic_consistency(["a", "b", "c", "d"]).entropy == pytest.approx(1.0)
    with pytest.raises(ValueError, match="at least one"):
        match_share([])
    with pytest.raises(ValueError, match="medium"):
        confidence_level(0.5, high=0.5, medium=0.8)
