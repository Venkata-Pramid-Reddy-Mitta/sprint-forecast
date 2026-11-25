"""Validate and describe a team's throughput history before anything samples from it.

This module exists so that every bad input is refused at one boundary with a typed
error, rather than surfacing later as a NaN percentile or a silent empty sample. The
forecast engine is allowed to assume its input is already clean because it only ever
receives a ThroughputHistory built here.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .errors import InvalidInput


@dataclass(frozen=True)
class ThroughputHistory:
    """A cleaned, non-negative throughput series plus the summary a report needs.

    `values` is the per-sprint count of items the team actually completed. Order is
    preserved for display but is irrelevant to the bootstrap, which treats the series
    as an unordered sample (see ADR-001 for why that assumption is deliberate and what
    it gives up).
    """

    values: tuple[float, ...]

    @property
    def n(self) -> int:
        return len(self.values)

    @property
    def mean(self) -> float:
        return float(np.mean(self.values))

    @property
    def nonzero_count(self) -> int:
        return int(sum(1 for v in self.values if v > 0))

    def as_array(self) -> np.ndarray:
        return np.asarray(self.values, dtype=float)


def validate_history(raw: object) -> ThroughputHistory:
    """Turn arbitrary caller input into a ThroughputHistory or raise InvalidInput.

    Rejected, each for a concrete reason a forecast cannot survive:
      - not a sequence, or empty: there is nothing to sample from;
      - a non-numeric or boolean entry: a count is a number, and bool sneaks through
        numeric checks because it subclasses int, so it is refused explicitly;
      - a negative or non-finite entry: throughput below zero is not a thing;
      - an all-zero history: every bootstrap sample sums to zero, so no backlog ever
        burns down and no percentile exists.
    """
    if isinstance(raw, (str, bytes)) or not hasattr(raw, "__iter__"):
        raise InvalidInput("throughput history must be a sequence of numbers")
    values = list(raw)
    if not values:
        raise InvalidInput("throughput history is empty; nothing to sample from")
    cleaned: list[float] = []
    for i, v in enumerate(values):
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            raise InvalidInput(f"throughput at index {i} is not a number: {v!r}")
        fv = float(v)
        if not np.isfinite(fv):
            raise InvalidInput(f"throughput at index {i} is not finite: {v!r}")
        if fv < 0:
            raise InvalidInput(f"throughput at index {i} is negative: {v!r}")
        cleaned.append(fv)
    if all(v == 0 for v in cleaned):
        raise InvalidInput("every recorded sprint completed zero items; cannot forecast")
    return ThroughputHistory(values=tuple(cleaned))


def validate_backlog(raw: object) -> float:
    """A backlog must be a positive, finite number of items. Zero is refused: a
    backlog of nothing has no completion date to forecast, which is a caller bug, not
    a forecast of 'done today'."""
    if isinstance(raw, bool) or not isinstance(raw, (int, float)):
        raise InvalidInput(f"backlog must be a number, got {raw!r}")
    fv = float(raw)
    if not np.isfinite(fv):
        raise InvalidInput(f"backlog is not finite: {raw!r}")
    if fv <= 0:
        raise InvalidInput(f"backlog must be positive, got {fv}")
    return fv
