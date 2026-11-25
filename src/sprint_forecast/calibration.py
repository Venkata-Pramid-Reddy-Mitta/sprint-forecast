"""Does a P85 date actually get hit 85 percent of the time? Measure it, do not assume it.

A forecaster that prints percentiles is easy. A forecaster whose P85 is empirically a
P85 is the only kind worth trusting. This module runs the only honest test of that: build
many synthetic teams from a known true throughput distribution, forecast each from a short
observed history, then draw a fresh future from the same true distribution and check how
often the realised outcome landed at or under each predicted percentile.

The expected and published result is that a bootstrap over a short history under-covers
its upper percentiles, because it can only resample values it has already seen and so
cannot represent a tail it has not yet observed. Experiment 4 sweeps history length to show
where that gap closes. Publishing the gap is the point: it is what tells a user when the
history is too short to commit on.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np

from .config import ForecastConfig
from .errors import ForecastError
from .forecast import ABSOLUTE_SPRINT_CAP, forecast

Sampler = Callable[[np.random.Generator, int], np.ndarray]


def negbinom_sampler(mean: float = 8.0, dispersion: float = 2.0) -> Sampler:
    """A negative-binomial throughput generator, overdispersed so variance exceeds the
    mean the way a real team's velocity does. dispersion is variance divided by mean;
    dispersion 1 would be Poisson. Parameterised through (mean, dispersion) because those
    are the quantities a delivery lead can reason about, not numpy's (n, p)."""
    if mean <= 0:
        raise ValueError("mean must be positive")
    if dispersion <= 1.0:
        raise ValueError("dispersion must exceed 1 for a negative binomial; use >1")
    r = mean / (dispersion - 1.0)  # number of failures parameter
    p = r / (r + mean)

    def sample(rng: np.random.Generator, size: int) -> np.ndarray:
        return rng.negative_binomial(r, p, size=size).astype(float)

    return sample


def _true_completion_sprints(rng: np.random.Generator, sampler: Sampler, backlog: float) -> int:
    """One realised future: draw true throughput sprint by sprint until the backlog is
    burned down, and return the sprint count. Capped identically to the forecaster so the
    two are compared on the same terms."""
    cum = 0.0
    for sprint in range(1, ABSOLUTE_SPRINT_CAP + 1):
        cum += float(sampler(rng, 1)[0])
        if cum >= backlog:
            return sprint
    return ABSOLUTE_SPRINT_CAP + 1  # did not finish; counts as not covered


@dataclass(frozen=True)
class CoverageResult:
    """Empirical coverage of each nominal percentile over `valid_teams` synthetic teams."""

    history_len: int
    n_teams: int
    valid_teams: int
    backlog: float
    nominal: dict[int, float]
    empirical: dict[int, float]
    mean_gap_p50_p85_sprints: float
    resolution_floor: float

    def worst_gap(self) -> tuple[int, float]:
        """The percentile with the largest shortfall of empirical below nominal, and the
        size of that shortfall in percentage points. The uncomfortable number."""
        gaps = {p: self.nominal[p] - self.empirical[p] for p in self.nominal}
        p = max(gaps, key=lambda k: gaps[k])
        return p, gaps[p] * 100.0


def run_coverage(
    sampler: Sampler,
    history_len: int,
    n_teams: int,
    backlog: float,
    config: ForecastConfig | None = None,
    base_seed: int = 7_000_000,
) -> CoverageResult:
    """Build `n_teams` teams, forecast each, and measure how often reality fell under the
    prediction. The team's observed history and its realised future are drawn from the same
    seeded stream (independent sequential draws); the bootstrap inside the forecast uses a
    disjoint seed so the forecaster never peeks at the future it is being graded against."""
    cfg = config or ForecastConfig()
    percentiles = cfg.percentiles
    covered = {p: 0 for p in percentiles}
    counted = {p: 0 for p in percentiles}
    gaps: list[float] = []
    valid_teams = 0

    for t in range(n_teams):
        team_rng = np.random.default_rng(base_seed + t)
        history = sampler(team_rng, history_len)
        try:
            fc = forecast(history, backlog, cfg.with_seed(base_seed + 500_000_000 + t))
        except ForecastError:
            continue  # a degenerate draw the forecaster rightly refused; not counted
        realised = _true_completion_sprints(team_rng, sampler, backlog)
        valid_teams += 1
        for p in percentiles:
            pred = fc.percentile_sprints[p]
            if pred is None:
                continue  # unbounded at this percentile; excluded from its coverage
            counted[p] += 1
            if realised <= pred:
                covered[p] += 1
        p50, p85 = fc.percentile_sprints.get(50), fc.percentile_sprints.get(85)
        if p50 is not None and p85 is not None:
            gaps.append(float(p85 - p50))

    empirical = {p: (covered[p] / counted[p] if counted[p] else float("nan")) for p in percentiles}
    return CoverageResult(
        history_len=history_len,
        n_teams=n_teams,
        valid_teams=valid_teams,
        backlog=backlog,
        nominal={p: p / 100.0 for p in percentiles},
        empirical=empirical,
        mean_gap_p50_p85_sprints=(float(np.mean(gaps)) if gaps else float("nan")),
        resolution_floor=(1.0 / valid_teams if valid_teams else float("nan")),
    )
