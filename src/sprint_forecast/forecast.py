"""The Monte Carlo throughput forecaster: the one thing this repository is about.

A committed delivery date is a point. A point has no probability attached to it, which
is exactly why "are we going to make it" gets answered with a shrug. This module replaces
the point with a distribution built by resampling the team's own past sprints, and then
reads the committed date off that distribution as a probability.

The method is a stationary bootstrap: each simulated sprint draws, with replacement, a
throughput value the team has actually recorded, and a trial counts sprints until the
backlog is burned down. Ten thousand trials give a distribution of completion sprints.
ADR-001 records why resampling observed history beats fitting a parametric curve here,
and ADR-004 records what that assumption cannot see.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from .config import ForecastConfig
from .errors import UnboundedForecast
from .throughput import ThroughputHistory, validate_backlog, validate_history

# Hard ceiling on simulated sprints regardless of config, so a near-stalled team cannot
# make the engine allocate an unbounded amount of work. A team that needs more than this
# many sprints is reported as unbounded, which is the honest answer anyway.
ABSOLUTE_SPRINT_CAP = 2000


@dataclass(frozen=True)
class Forecast:
    """The result of one forecast. Sprint counts are the primary output; dates are
    derived in the report layer, because a sprint count is machine independent and a
    calendar date is not (see ADR-002)."""

    n_history: int
    mean_throughput: float
    backlog: float
    trials: int
    naive_sprints: int
    cap_sprints: int
    not_reached_fraction: float
    percentile_sprints: dict[int, int | None]
    histogram: dict[int, int]
    committed_sprints: int | None
    prob_meet_committed: float | None
    confidence_target: float

    @property
    def p50(self) -> int | None:
        return self.percentile_sprints.get(50)

    @property
    def verdict(self) -> str | None:
        """safe, unsafe, or None when no commitment was supplied. A commitment is safe
        when its probability of being met clears the configured confidence target."""
        if self.prob_meet_committed is None:
            return None
        return "safe" if self.prob_meet_committed >= self.confidence_target else "unsafe"

    @property
    def committed_below_p50(self) -> bool | None:
        """True when the committed date is a coin flip or worse: less likely than not.
        This is the headline the repository is built to surface."""
        if self.prob_meet_committed is None:
            return None
        return self.prob_meet_committed < 0.5


def _percentile_higher(sorted_counts: np.ndarray, p: int, sentinel: int) -> int | None:
    """Conservative percentile: the smallest sprint count at or above which `p` percent
    of trials finished. Uses the 'higher' convention so a reported P85 is a sprint the
    team genuinely hit in at least 85 percent of trials, never an interpolated fraction
    of a sprint. Returns None when the percentile falls inside the unreached tail."""
    value = int(np.percentile(sorted_counts, p, method="higher"))
    return None if value >= sentinel else value


def forecast(
    history: object,
    backlog: object,
    config: ForecastConfig | None = None,
    committed_sprints: int | None = None,
) -> Forecast:
    """Forecast completion of `backlog` items from a team's throughput `history`.

    Raises InvalidInput (via the validators) for data that cannot be forecast, and
    UnboundedForecast when too many trials fail to finish within the cap. The caller
    maps both to a non-zero "could not answer" exit code; a low probability on a valid
    forecast is a "the answer is no" result, not an error.
    """
    cfg = config or ForecastConfig()
    hist: ThroughputHistory = validate_history(history)
    back = validate_backlog(backlog)

    naive = max(1, math.ceil(back / hist.mean))
    # The cap is bounded absolutely so a near-stalled team cannot force an unbounded
    # simulation. When the naive estimate alone exceeds the absolute cap, the cap wins
    # and the forecast comes back unbounded, which is the honest answer for such a team.
    desired = max(naive + 1, int(math.ceil(cfg.max_sprints_multiple * naive)))
    cap = min(desired, ABSOLUTE_SPRINT_CAP)
    sentinel = cap + 1

    rng = np.random.default_rng(cfg.seed)
    source = hist.as_array()
    n = hist.n

    cum = np.zeros(cfg.trials, dtype=float)
    done_at = np.zeros(cfg.trials, dtype=np.int64)  # 0 means not finished yet
    for sprint in range(1, cap + 1):
        draws = source[rng.integers(0, n, size=cfg.trials)]
        cum += draws
        newly_done = (done_at == 0) & (cum >= back)
        done_at[newly_done] = sprint
        if done_at.all():
            break

    not_reached = done_at == 0
    not_reached_fraction = float(np.mean(not_reached))
    if not_reached_fraction > cfg.unbounded_fraction:
        raise UnboundedForecast(
            f"{not_reached_fraction:.0%} of trials did not finish within {cap} sprints; "
            "throughput is too often zero to forecast a date"
        )

    done_at[not_reached] = sentinel
    sorted_counts = np.sort(done_at)

    percentile_sprints: dict[int, int | None] = {
        p: _percentile_higher(sorted_counts, p, sentinel) for p in cfg.percentiles
    }

    finished = done_at[~not_reached]
    hist_counts = np.bincount(finished) if finished.size else np.zeros(1, dtype=int)
    histogram = {int(s): int(c) for s, c in enumerate(hist_counts) if c > 0}

    prob_meet: float | None = None
    if committed_sprints is not None:
        if committed_sprints < 1:
            from .errors import InvalidInput

            raise InvalidInput("committed_sprints must be at least 1")
        prob_meet = float(np.mean(done_at <= committed_sprints))

    return Forecast(
        n_history=hist.n,
        mean_throughput=hist.mean,
        backlog=back,
        trials=cfg.trials,
        naive_sprints=naive,
        cap_sprints=cap,
        not_reached_fraction=not_reached_fraction,
        percentile_sprints=percentile_sprints,
        histogram=histogram,
        committed_sprints=committed_sprints,
        prob_meet_committed=prob_meet,
        confidence_target=cfg.confidence_target,
    )
