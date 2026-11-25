"""The calibration engine is the credibility core, so its own behaviour is pinned here."""

from __future__ import annotations

import numpy as np
import pytest

from sprint_forecast.calibration import (
    CoverageResult,
    negbinom_sampler,
    run_coverage,
)
from sprint_forecast.config import ForecastConfig

FAST = ForecastConfig(trials=600)


def test_the_negbinom_sampler_has_the_requested_mean_and_overdispersion():
    rng = np.random.default_rng(0)
    draws = negbinom_sampler(mean=8.0, dispersion=2.0)(rng, 50_000)
    assert abs(draws.mean() - 8.0) < 0.2
    assert draws.var() > draws.mean()  # overdispersed, as asked


@pytest.mark.parametrize("disp", [1.0, 0.5])
def test_a_dispersion_of_one_or_less_is_rejected(disp):
    with pytest.raises(ValueError, match="dispersion"):
        negbinom_sampler(mean=8.0, dispersion=disp)


def test_a_non_positive_mean_is_rejected():
    with pytest.raises(ValueError, match="mean"):
        negbinom_sampler(mean=0.0)


def test_coverage_runs_and_reports_a_probability_per_nominal_percentile():
    r = run_coverage(negbinom_sampler(), history_len=8, n_teams=300, backlog=64.0, config=FAST)
    assert isinstance(r, CoverageResult)
    assert r.valid_teams > 0
    for p in (50, 70, 85, 95):
        assert 0.0 <= r.empirical[p] <= 1.0
        assert r.nominal[p] == p / 100.0


def test_the_resolution_floor_is_one_over_the_valid_team_count():
    r = run_coverage(negbinom_sampler(), history_len=8, n_teams=200, backlog=64.0, config=FAST)
    assert r.resolution_floor == pytest.approx(1.0 / r.valid_teams)


def test_worst_gap_names_a_percentile_and_a_shortfall_in_points():
    r = run_coverage(negbinom_sampler(), history_len=6, n_teams=300, backlog=64.0, config=FAST)
    percentile, points = r.worst_gap()
    assert percentile in (50, 70, 85, 95)
    assert isinstance(points, float)


def test_a_longer_history_covers_the_p95_tail_at_least_as_well_as_a_short_one():
    """The central claim: short histories under-cover the tail because the bootstrap
    cannot resample values it has not seen. Longer history should not cover worse."""
    short = run_coverage(negbinom_sampler(), history_len=5, n_teams=800, backlog=64.0, config=FAST)
    long = run_coverage(negbinom_sampler(), history_len=40, n_teams=800, backlog=64.0, config=FAST)
    assert long.empirical[95] >= short.empirical[95] - 0.02


def test_coverage_is_deterministic_for_a_fixed_base_seed():
    a = run_coverage(negbinom_sampler(), history_len=8, n_teams=200, backlog=64.0, config=FAST)
    b = run_coverage(negbinom_sampler(), history_len=8, n_teams=200, backlog=64.0, config=FAST)
    assert a.empirical == b.empirical


def test_a_future_that_never_progresses_is_reported_at_the_cap_plus_one():
    from sprint_forecast.calibration import _true_completion_sprints
    from sprint_forecast.forecast import ABSOLUTE_SPRINT_CAP

    zero = lambda rng, size: np.zeros(size)  # noqa: E731 - tiny local sampler
    assert _true_completion_sprints(np.random.default_rng(0), zero, backlog=10.0) == (
        ABSOLUTE_SPRINT_CAP + 1
    )


def test_teams_the_forecaster_refuses_are_skipped_not_counted():
    """When every drawn history is degenerate, each team is refused and no coverage is
    claimed: valid_teams is zero and the empirical rates are undefined rather than a
    flattering one from an empty sample."""
    zero = lambda rng, size: np.zeros(size)  # noqa: E731
    r = run_coverage(zero, history_len=6, n_teams=50, backlog=40.0, config=FAST)
    assert r.valid_teams == 0
    assert all(np.isnan(v) for v in r.empirical.values())
    assert np.isnan(r.resolution_floor)
