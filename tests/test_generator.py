"""The fixture must be deterministic and must not be secretly stacked."""

from __future__ import annotations

import math

from sprint_forecast.generator import (
    ARCHETYPES,
    build_scenarios,
    load_scenarios,
    write_scenarios,
)
from sprint_forecast.throughput import validate_history


def test_there_are_twelve_archetypes_and_twelve_scenarios():
    assert len(ARCHETYPES) == 12
    assert len(build_scenarios()) == 12


def test_the_fixture_is_deterministic_across_rebuilds():
    assert build_scenarios() == build_scenarios()


def test_every_generated_history_is_a_valid_throughput_series():
    for sc in build_scenarios():
        validate_history(sc["history"])  # must not raise


def test_the_holiday_gap_scenario_contains_a_zero_sprint():
    gap = next(s for s in build_scenarios() if s["name"] == "holiday-gap")
    assert 0 in gap["history"]


def test_a_sandbagged_commitment_sits_above_the_naive_estimate():
    sb = next(s for s in build_scenarios() if s["commit_policy"] == "sandbagged")
    naive = math.ceil(sb["backlog"] / (sum(sb["history"]) / len(sb["history"])))
    assert sb["committed_sprints"] > naive


def test_an_optimistic_commitment_sits_below_the_naive_estimate():
    opt = next(s for s in build_scenarios() if s["commit_policy"] == "optimistic")
    naive = math.ceil(opt["backlog"] / (sum(opt["history"]) / len(opt["history"])))
    assert opt["committed_sprints"] < naive


def test_the_fixture_mixes_policies_so_it_is_not_stacked_one_way():
    policies = {s["commit_policy"] for s in build_scenarios()}
    assert {"optimistic", "stretch", "buffered", "sandbagged"} <= policies


def test_write_then_load_round_trips_the_scenarios(tmp_path):
    path = write_scenarios(tmp_path / "scenarios.json")
    loaded = load_scenarios(path)
    assert loaded == build_scenarios()
