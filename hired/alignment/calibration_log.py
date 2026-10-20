"""Collect held-out (score, truth) pairs from answered clarifications and fit a calibrator.

:func:`~hired.alignment.calibration.calibrate_match` needs scored judgments with known
truth. The truth arrives when the candidate answers a clarifying question
(:meth:`~hired.candidate.CandidateKnowledgeBase.record_qa`): the record's ``match_score``
*before* the answer, plus what the answer established. :class:`CalibrationLog` appends
each pair to the user's ``info/calibration/pairs.jsonl`` and, once both classes have enough
pairs for the chosen levels, fits and persists a :class:`MatchCalibrator`
(``info/calibration/calibrator.json``) that the ``hired-align`` workflow loads with
:meth:`CalibrationLog.load_calibrator`.

Keep these pairs out of anything used to tune the scoring: the conformal bound only holds
for data the scorer never saw.

>>> import tempfile
>>> from hired.persistence.base import UserStore
>>> log = CalibrationLog(UserStore("t", root=tempfile.mkdtemp()))
>>> log.add(0.9, True, qa_id="qa-1")
>>> log.pairs()
[(0.9, True)]
>>> log.fit() is None  # too few pairs for the default levels
True
"""

from __future__ import annotations

import json
import math
import os
from collections.abc import Callable

from hired.alignment.calibration import (
    DFLT_FALSE_ACCEPT_RATE,
    DFLT_MISS_RATE,
    MatchCalibrator,
    calibrate_match,
)
from hired.persistence.base import UserStore, read_json_file, write_json_file

__all__ = ["CalibrationLog", "min_pairs"]

CALIBRATION_DIR = "calibration"
PAIRS_FILE = "pairs.jsonl"
CALIBRATOR_FILE = "calibrator.json"


def min_pairs(rate: float) -> int:
    """Pairs a class needs for a finite threshold at ``rate``: ``ceil(1/rate) - 1``.

    >>> min_pairs(0.05), min_pairs(0.1)
    (19, 9)
    """
    return math.ceil(1 / rate) - 1


class CalibrationLog:
    """The user's calibration pairs and fitted calibrator, kept under ``info/calibration/``."""

    def __init__(
        self,
        store: UserStore | None = None,
        *,
        false_accept_rate: float = DFLT_FALSE_ACCEPT_RATE,
        miss_rate: float = DFLT_MISS_RATE,
    ) -> None:
        self.store = store or UserStore()
        self.false_accept_rate, self.miss_rate = false_accept_rate, miss_rate

    def _path(self, name: str) -> str:
        return os.path.join(self.store._info(CALIBRATION_DIR), name)

    def add(self, match_score: float, truth: bool, *, qa_id: str | None = None) -> None:
        """Append one pair (the score before the answer, the truth the answer established)."""
        if not 0.0 <= match_score <= 1.0:
            raise ValueError(f"a match score must be in [0, 1], got {match_score!r}")
        path = self._path(PAIRS_FILE)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        row = {"score": float(match_score), "truth": bool(truth), "qa_id": qa_id}
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(row) + "\n")

    def rows(self) -> list[dict]:
        path = self._path(PAIRS_FILE)
        if not os.path.exists(path):
            return []
        with open(path, encoding="utf-8") as f:
            return [json.loads(line) for line in f if line.strip()]

    def pairs(self) -> list[tuple[float, bool]]:
        return [(r["score"], r["truth"]) for r in self.rows()]

    def ready(self) -> bool:
        """Whether each class has enough pairs for its level."""
        pairs = self.pairs()
        n_match = sum(y for _, y in pairs)
        return (
            n_match >= min_pairs(self.miss_rate)
            and len(pairs) - n_match >= min_pairs(self.false_accept_rate)
        )

    def fit(self, *, persist: bool = False) -> MatchCalibrator | None:
        """Fit on the logged pairs; ``None`` until :meth:`ready`. ``persist`` saves the result."""
        if not self.ready():
            return None
        scores, labels = zip(*self.pairs(), strict=True)
        cal = calibrate_match(
            scores, labels, false_accept_rate=self.false_accept_rate, miss_rate=self.miss_rate
        )
        if persist:
            write_json_file(self._path(CALIBRATOR_FILE), cal.to_dict())
        return cal

    def load_calibrator(self) -> MatchCalibrator | None:
        """The persisted calibrator, or ``None`` if none has been fitted yet."""
        d = read_json_file(self._path(CALIBRATOR_FILE))
        return MatchCalibrator.from_dict(d) if d else None

    def add_and_refit(
        self, match_score: float, truth: bool, *, qa_id: str | None = None
    ) -> MatchCalibrator | None:
        """:meth:`add` a pair, then refit and persist when ready; return the calibrator."""
        self.add(match_score, truth, qa_id=qa_id)
        return self.fit(persist=True)
