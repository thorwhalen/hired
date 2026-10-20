"""Calibrated confidence: multi-sample consistency and a conformal ask/auto-decide rule.

Self-reported confidence (an LLM saying "high") is overconfident; the honesty
contract needs a signal that is not. Two deterministic pieces, the judgments
themselves staying external (the ``hired-align`` skill or an injected LLM):

1. **Consistency.** Ask the same question several times and see how often the
   answers agree in meaning (:func:`semantic_consistency`). Agreement is the
   signal; :func:`match_share` turns sampled match states into a score in
   ``[0, 1]`` and :func:`confidence_level` into a :class:`ConfidenceLevel`.
2. **Conformal abstention.** On a held-out set of scored, labelled judgments,
   :func:`calibrate_match` fits a class-conditional (Mondrian) split-conformal
   rule. :meth:`MatchCalibrator.decide` then auto-accepts a match only when the
   score excludes "no match" at level ``false_accept_rate``, auto-rejects only
   when it excludes "match" at level ``miss_rate``, and otherwise says *ask*.

The guarantee: over calibration and test drawn alike (exchangeable), a true
non-match is auto-accepted with probability at most ``false_accept_rate``, and a
true match auto-rejected with probability at most ``miss_rate``. The asymmetry
("never exaggerate") is the choice of a smaller ``false_accept_rate``. With too
few calibration examples of a class to support its level, the rule never
auto-decides against that class: it asks.

See ``misc/docs/research/jd-candidate-matching.md`` (unknown vs absent) and #12.

>>> scores = [0.9, 0.95, 0.8, 1.0, 0.85] * 8 + [0.1, 0.2, 0.0, 0.3, 0.15] * 8
>>> labels = [True] * 40 + [False] * 40
>>> cal = calibrate_match(scores, labels, false_accept_rate=0.05, miss_rate=0.1)
>>> cal.decide(0.97), cal.decide(0.05), cal.decide(0.5)
(<Decision.AUTO_MATCH: 'auto_match'>, <Decision.AUTO_NO_MATCH: 'auto_no_match'>, <Decision.ASK: 'ask'>)
"""

from __future__ import annotations

import math
from collections import Counter
from collections.abc import Callable, Hashable, Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any

from hired.candidate.base import ConfidenceLevel, MatchState

__all__ = [
    "Consistency",
    "Decision",
    "MatchCalibrator",
    "calibrate_match",
    "conformal_quantile",
    "confidence_level",
    "match_share",
    "semantic_consistency",
]

#: Agreement at or above which a consistency reads as high, then as medium.
DFLT_HIGH_AGREEMENT, DFLT_MEDIUM_AGREEMENT = 0.9, 0.6
#: Default conformal levels: false accepts are held tighter than misses.
DFLT_FALSE_ACCEPT_RATE, DFLT_MISS_RATE = 0.05, 0.1


@dataclass(frozen=True)
class Consistency:
    """How far several sampled answers to one question agree.

    ``majority`` is the most common meaning (``None`` without samples),
    ``agreement`` its share, ``entropy`` the Shannon entropy of the meanings
    normalised to ``[0, 1]`` (0: all agree; 1: all differ), ``counts`` the
    number of samples per meaning.
    """

    majority: Hashable | None
    agreement: float
    entropy: float
    n_samples: int
    counts: Mapping[Hashable, int] = field(default_factory=dict)


def semantic_consistency(
    samples: Iterable[Any], *, meaning: Callable[[Any], Hashable] | None = None
) -> Consistency:
    """The agreement of sampled answers, clustered by ``meaning`` (default: equality).

    ``meaning`` maps an answer to its meaning: a normalised label, an entailment
    cluster id. Answers that mean the same count as agreeing however worded.

    >>> c = semantic_consistency(["Yes", "yes", "no", "YES "], meaning=lambda s: s.strip().lower())
    >>> c.majority, c.agreement, round(c.entropy, 3)
    ('yes', 0.75, 0.811)
    >>> semantic_consistency([]).agreement
    0.0
    """
    key = meaning or (lambda x: x)
    counts = Counter(key(s) for s in samples)
    n = sum(counts.values())
    if not n:
        return Consistency(None, 0.0, 1.0, 0, {})
    majority, top = counts.most_common(1)[0]
    if len(counts) == 1:
        entropy = 0.0
    else:
        h = -sum(c / n * math.log(c / n) for c in counts.values())
        entropy = h / math.log(min(n, max(len(counts), 2)))
    return Consistency(majority, top / n, min(entropy, 1.0), n, dict(counts))


def match_share(
    samples: Iterable[Any], *, is_match: Callable[[Any], bool] | None = None
) -> float:
    """The share of sampled judgments that say "match": a score in ``[0, 1]``.

    By default a sample matches when it is (or names) :attr:`MatchState.CONFIRMED`;
    ``is_match`` overrides that. This is the score :func:`calibrate_match` takes.

    >>> match_share(["confirmed", "confirmed", "unknown", "contradicted"])
    0.5
    """
    test = is_match or (lambda s: MatchState(s) == MatchState.CONFIRMED)
    flags = [bool(test(s)) for s in samples]
    if not flags:
        raise ValueError("match_share needs at least one sample")
    return sum(flags) / len(flags)


def confidence_level(
    agreement: Consistency | float,
    *,
    high: float = DFLT_HIGH_AGREEMENT,
    medium: float = DFLT_MEDIUM_AGREEMENT,
) -> ConfidenceLevel:
    """A :class:`ConfidenceLevel` from sampled agreement rather than self-report.

    >>> confidence_level(0.95), confidence_level(0.7), confidence_level(0.5)
    (<ConfidenceLevel.HIGH: 'high'>, <ConfidenceLevel.MEDIUM: 'medium'>, <ConfidenceLevel.LOW: 'low'>)
    """
    if not 0 <= medium <= high <= 1:
        raise ValueError(f"need 0 <= medium <= high <= 1, got {medium=}, {high=}")
    a = agreement.agreement if isinstance(agreement, Consistency) else float(agreement)
    if a >= high:
        return ConfidenceLevel.HIGH
    return ConfidenceLevel.MEDIUM if a >= medium else ConfidenceLevel.LOW


def conformal_quantile(scores: Sequence[float], alpha: float) -> float:
    """The split-conformal threshold: the ``ceil((n+1)(1-alpha))``-th smallest score.

    A new score drawn like these exceeds it with probability at most ``alpha``.
    When ``n`` is too small for ``alpha`` (``ceil((n+1)(1-alpha)) > n``) no finite
    threshold has that guarantee, and this returns ``inf``.

    >>> conformal_quantile([0.1, 0.2, 0.3, 0.4], 0.2)  # ceil(5 * 0.8) = 4th
    0.4
    >>> conformal_quantile([0.1, 0.2], 0.1)
    inf
    """
    if not 0 < alpha < 1:
        raise ValueError(f"alpha must be in (0, 1), got {alpha!r}")
    n = len(scores)
    rank = math.ceil((n + 1) * (1 - alpha))
    if rank > n:
        return math.inf
    return sorted(scores)[rank - 1]


class Decision(str, Enum):
    """What to do with a judgment: take it as a match, as no match, or ask."""

    AUTO_MATCH = "auto_match"
    AUTO_NO_MATCH = "auto_no_match"
    ASK = "ask"


@dataclass(frozen=True)
class MatchCalibrator:
    """A fitted class-conditional conformal rule over a match score ``s`` in ``[0, 1]``.

    "Match" stays in the prediction set while its nonconformity ``1 - s`` is at most
    ``match_threshold``; "no match" while ``s`` is at most ``no_match_threshold``.
    A singleton set decides; two labels (or none) mean ask. JSON-ready through
    :meth:`to_dict` / :meth:`from_dict`, so a fitted rule can be stored and reviewed.
    """

    match_threshold: float
    no_match_threshold: float
    false_accept_rate: float = DFLT_FALSE_ACCEPT_RATE
    miss_rate: float = DFLT_MISS_RATE
    n_match: int = 0
    n_no_match: int = 0

    def prediction_set(self, score: float) -> frozenset[bool]:
        """The labels (``True``: match) not excluded at their levels."""
        s = _unit(score)
        labels = set()
        if 1 - s <= self.match_threshold:
            labels.add(True)
        if s <= self.no_match_threshold:
            labels.add(False)
        return frozenset(labels)

    def decide(self, score: float) -> Decision:
        """Auto-decide on a singleton prediction set; otherwise ask."""
        labels = self.prediction_set(score)
        if labels == {True}:
            return Decision.AUTO_MATCH
        if labels == {False}:
            return Decision.AUTO_NO_MATCH
        return Decision.ASK

    def to_dict(self) -> dict[str, Any]:
        """A JSON-ready dict (an infinite threshold is written as ``None``)."""
        d = asdict(self)
        for k in ("match_threshold", "no_match_threshold"):
            if math.isinf(d[k]):
                d[k] = None
        return d

    @classmethod
    def from_dict(cls, d: Mapping[str, Any]) -> MatchCalibrator:
        """Inverse of :meth:`to_dict`."""
        d = dict(d)
        for k in ("match_threshold", "no_match_threshold"):
            d[k] = math.inf if d.get(k) is None else float(d[k])
        return cls(**d)


def calibrate_match(
    scores: Iterable[float],
    labels: Iterable[bool],
    *,
    false_accept_rate: float = DFLT_FALSE_ACCEPT_RATE,
    miss_rate: float = DFLT_MISS_RATE,
) -> MatchCalibrator:
    """Fit the ask/auto-decide rule on held-out judgments with known truth.

    ``scores`` are match scores in ``[0, 1]`` (say :func:`match_share` of sampled
    judgments), ``labels`` whether each was truly a match. Each class gets its own
    threshold (Mondrian split conformal): ``false_accept_rate`` bounds how often a
    true non-match is auto-accepted, ``miss_rate`` how often a true match is
    auto-rejected. Keep the held-out set apart from anything used to tune the
    scoring, or the bound does not hold.
    """
    pairs = [(_unit(s), bool(y)) for s, y in zip(scores, labels, strict=True)]
    match = [1 - s for s, y in pairs if y]
    no_match = [s for s, y in pairs if not y]
    return MatchCalibrator(
        match_threshold=conformal_quantile(match, miss_rate) if match else math.inf,
        no_match_threshold=conformal_quantile(no_match, false_accept_rate)
        if no_match
        else math.inf,
        false_accept_rate=false_accept_rate,
        miss_rate=miss_rate,
        n_match=len(match),
        n_no_match=len(no_match),
    )


def _unit(score: float) -> float:
    s = float(score)
    if not 0.0 <= s <= 1.0:
        raise ValueError(f"a match score must be in [0, 1], got {score!r}")
    return s
