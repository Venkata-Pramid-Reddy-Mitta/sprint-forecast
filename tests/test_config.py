"""The config object is the only place a policy lives, so its validation is load bearing."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from sprint_forecast.config import DEFAULT_PERCENTILES, ForecastConfig


def test_default_config_is_valid_and_has_the_documented_target():
    cfg = ForecastConfig()
    assert cfg.confidence_target == 0.85
    assert cfg.percentiles == DEFAULT_PERCENTILES
    assert 50 in cfg.percentiles and 85 in cfg.percentiles


def test_trials_below_one_is_rejected():
    with pytest.raises(ValueError, match="trials"):
        ForecastConfig(trials=0)


@pytest.mark.parametrize("target", [0.0, 1.0, -0.1, 1.5])
def test_confidence_target_must_be_strictly_between_zero_and_one(target):
    with pytest.raises(ValueError, match="confidence_target"):
        ForecastConfig(confidence_target=target)


def test_empty_percentiles_is_rejected():
    with pytest.raises(ValueError, match="percentile"):
        ForecastConfig(percentiles=())


@pytest.mark.parametrize("pcts", [(0, 50), (50, 100), (50, 101)])
def test_percentiles_outside_the_open_interval_are_rejected(pcts):
    with pytest.raises(ValueError, match="percentiles"):
        ForecastConfig(percentiles=pcts)


def test_max_sprints_multiple_must_exceed_one():
    with pytest.raises(ValueError, match="max_sprints_multiple"):
        ForecastConfig(max_sprints_multiple=1.0)


@pytest.mark.parametrize("frac", [0.0, 1.0, 2.0])
def test_unbounded_fraction_must_be_strictly_between_zero_and_one(frac):
    with pytest.raises(ValueError, match="unbounded_fraction"):
        ForecastConfig(unbounded_fraction=frac)


def test_sprint_days_below_one_is_rejected():
    with pytest.raises(ValueError, match="sprint_days"):
        ForecastConfig(sprint_days=0)


def test_with_seed_returns_a_copy_with_only_the_seed_changed():
    cfg = ForecastConfig(trials=500)
    other = cfg.with_seed(999)
    assert other.seed == 999
    assert other.trials == 500
    assert cfg.seed != 999  # original is untouched because the dataclass is frozen


def test_config_is_frozen_so_a_forecast_cannot_be_reconfigured_mid_run():
    cfg = ForecastConfig()
    with pytest.raises(FrozenInstanceError):
        cfg.trials = 1  # type: ignore[misc]
