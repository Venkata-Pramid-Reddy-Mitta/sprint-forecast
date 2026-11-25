"""Properties of the forecast engine, including the bug that the cap once hid."""

from __future__ import annotations

import pytest

from sprint_forecast.config import ForecastConfig
from sprint_forecast.errors import InvalidInput, UnboundedForecast
from sprint_forecast.forecast import ABSOLUTE_SPRINT_CAP, forecast

STEADY = [8, 5, 9, 7, 6, 10, 4, 8]


def test_percentiles_are_monotonic_non_decreasing():
    fc = forecast(STEADY, 60)
    sprints = [fc.percentile_sprints[p] for p in (50, 70, 85, 95)]
    assert sprints == sorted(sprints)


def test_the_same_seed_gives_identical_percentiles():
    a = forecast(STEADY, 60).percentile_sprints
    b = forecast(STEADY, 60).percentile_sprints
    assert a == b


def test_a_different_seed_can_change_the_distribution_but_not_wildly():
    a = forecast(STEADY, 60, ForecastConfig(seed=1))
    b = forecast(STEADY, 60, ForecastConfig(seed=2))
    assert abs(a.p50 - b.p50) <= 1  # stable to the sprint across seeds


def test_a_probability_of_meeting_a_date_is_between_zero_and_one():
    fc = forecast(STEADY, 60, committed_sprints=9)
    assert 0.0 <= fc.prob_meet_committed <= 1.0


def test_an_easy_commitment_is_safe_and_a_hard_one_is_unsafe():
    easy = forecast(STEADY, 60, committed_sprints=15)
    hard = forecast(STEADY, 60, committed_sprints=6)
    assert easy.verdict == "safe"
    assert hard.verdict == "unsafe"


def test_a_commitment_below_p50_is_flagged_as_a_coin_flip_or_worse():
    fc = forecast(STEADY, 60, committed_sprints=6)
    assert fc.committed_below_p50 is True


def test_a_commitment_above_p50_is_not_flagged_below_p50():
    fc = forecast(STEADY, 60, committed_sprints=20)
    assert fc.committed_below_p50 is False


def test_without_a_commitment_there_is_no_verdict_and_no_probability():
    fc = forecast(STEADY, 60)
    assert fc.verdict is None
    assert fc.prob_meet_committed is None
    assert fc.committed_below_p50 is None


def test_a_higher_confidence_target_can_flip_a_verdict_to_unsafe():
    lenient = forecast(STEADY, 60, ForecastConfig(confidence_target=0.5), committed_sprints=9)
    strict = forecast(STEADY, 60, ForecastConfig(confidence_target=0.99), committed_sprints=9)
    assert lenient.verdict == "safe"
    assert strict.verdict == "unsafe"


def test_the_histogram_counts_only_trials_that_finished():
    cfg = ForecastConfig(trials=500)
    fc = forecast(STEADY, 60, cfg)
    reached = round((1 - fc.not_reached_fraction) * cfg.trials)
    assert sum(fc.histogram.values()) == reached


def test_naive_estimate_is_backlog_over_mean_rounded_up():
    fc = forecast([10, 10, 10], 55)  # mean 10, naive ceil(5.5)=6
    assert fc.naive_sprints == 6


def test_committed_sprints_below_one_is_rejected_as_invalid_input():
    with pytest.raises(InvalidInput, match="committed_sprints"):
        forecast(STEADY, 60, committed_sprints=0)


def test_an_unreachable_backlog_is_reported_unbounded_not_given_a_fake_date():
    with pytest.raises(UnboundedForecast, match="did not finish"):
        forecast([0, 0, 0, 0, 1], backlog=600)


def test_a_near_stalled_team_capped_at_the_absolute_cap_is_unbounded():
    """Pins a real bug found during the build.

    The cap was once computed as max(naive + 1, min(multiple * naive, ABSOLUTE_CAP)).
    For a team whose naive estimate alone exceeded the absolute cap, the max() put the
    cap back above ABSOLUTE_SPRINT_CAP, so the engine would loop naive+1 times (here
    3001) instead of stopping at the guard. The symptom was an UnboundedForecast message
    quoting 3001 sprints when the absolute cap was 2000: the guard was there but not
    guarding. The fix clamps the cap with a final min() against ABSOLUTE_SPRINT_CAP, so
    a team that needs more sprints than we simulate is simply reported unbounded. This
    test fails against the old expression and passes against the fixed one.
    """
    with pytest.raises(UnboundedForecast) as exc:
        forecast([0, 0, 0, 0, 1], backlog=600, config=ForecastConfig(max_sprints_multiple=10.0))
    assert str(ABSOLUTE_SPRINT_CAP) in str(exc.value)


def test_a_wider_backlog_never_finishes_sooner_than_a_narrower_one():
    narrow = forecast(STEADY, 40).p50
    wide = forecast(STEADY, 80).p50
    assert wide >= narrow


def test_mean_throughput_is_reported_from_the_history():
    fc = forecast([4, 6], 10)
    assert fc.mean_throughput == 5.0
