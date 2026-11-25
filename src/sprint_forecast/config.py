"""One place for every policy a reviewer might want to argue with.

Nothing in the forecasting code reads a bare literal for a threshold, a trial count
or a percentile. They all come from here, so a reviewer can change the confidence
target or the simulation size in one obvious place and rerun, and so the defence
guide can point at a single file when asked "where did 85 percent come from".
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace

# Percentiles the report always computes. P50 is the coin-flip date, P85 is the
# conventional "commit-with-a-buffer" date. They are policy, not physics, hence here.
DEFAULT_PERCENTILES: tuple[int, ...] = (50, 70, 85, 95)


@dataclass(frozen=True)
class ForecastConfig:
    """Immutable so a forecast cannot be silently reconfigured mid-run.

    trials
        Monte Carlo sample size. Larger is steadier but slower. The default is
        chosen so the published percentiles are stable to the sprint across seeds
        (see experiment 4), not for speed.
    confidence_target
        The probability a committed date must clear to be called safe. 0.85 is the
        default because the P85 date is the one most delivery teams are taught to
        commit to. Changing it changes the exit code, not the forecast.
    max_sprints_multiple
        A trial is capped at this multiple of the naive estimate (backlog divided by
        mean throughput). A run that hits the cap too often is reported as unbounded
        rather than finished, so a near-stalled team never gets a flattering date.
    unbounded_fraction
        If more than this fraction of trials hit the cap, the forecast is unbounded.
    sprint_days
        Calendar length of one sprint, used only to translate a sprint count into a
        date. The headline numbers are sprint counts; the date is a convenience.
    seed
        The RNG seed. Fixed by default so every published number reproduces exactly.
    """

    trials: int = 10_000
    confidence_target: float = 0.85
    percentiles: tuple[int, ...] = field(default_factory=lambda: DEFAULT_PERCENTILES)
    max_sprints_multiple: float = 10.0
    unbounded_fraction: float = 0.05
    sprint_days: int = 14
    seed: int = 20260501

    def __post_init__(self) -> None:
        if self.trials < 1:
            raise ValueError("trials must be at least 1")
        if not 0.0 < self.confidence_target < 1.0:
            raise ValueError("confidence_target must be strictly between 0 and 1")
        if not self.percentiles:
            raise ValueError("at least one percentile is required")
        if any(not 0 < p < 100 for p in self.percentiles):
            raise ValueError("percentiles must be strictly between 0 and 100")
        if self.max_sprints_multiple <= 1.0:
            raise ValueError("max_sprints_multiple must exceed 1")
        if not 0.0 < self.unbounded_fraction < 1.0:
            raise ValueError("unbounded_fraction must be strictly between 0 and 1")
        if self.sprint_days < 1:
            raise ValueError("sprint_days must be at least 1")

    def with_seed(self, seed: int) -> ForecastConfig:
        """Return a copy with a different seed, for the per-team draws in calibration."""
        return replace(self, seed=seed)
