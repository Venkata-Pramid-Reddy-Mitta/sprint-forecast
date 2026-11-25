"""The CLI's exit codes are its contract, so each path is pinned to a specific code."""

from __future__ import annotations

import io
import json

import pytest

from sprint_forecast.cli import (
    EXIT_CANNOT_ANSWER,
    EXIT_SAFE,
    EXIT_UNSAFE,
    _parse_history,
    main,
)

FAST = ["--trials", "500"]


def run(argv):
    out = io.StringIO()
    code = main(argv, out=out)
    return code, out.getvalue()


def test_parse_history_accepts_both_commas_and_spaces():
    assert _parse_history("8, 5 9,7") == [8.0, 5.0, 9.0, 7.0]


def test_a_safe_commitment_exits_zero():
    code, out = run([*FAST, "forecast", "--history", "8 5 9 7 6 10 4 8",
                     "--backlog", "60", "--committed", "15"])
    assert code == EXIT_SAFE
    assert "SAFE" in out


def test_an_unsafe_commitment_exits_two():
    code, out = run([*FAST, "forecast", "--history", "8 5 9 7 6 10 4 8",
                     "--backlog", "60", "--committed", "6"])
    assert code == EXIT_UNSAFE
    assert "UNSAFE" in out


def test_an_unforecastable_input_exits_three():
    code, _ = run([*FAST, "forecast", "--history", "0 0 0 0 1", "--backlog", "600"])
    assert code == EXIT_CANNOT_ANSWER


def test_an_invalid_history_exits_three():
    code, _ = run([*FAST, "forecast", "--history", "0 0 0", "--backlog", "40"])
    assert code == EXIT_CANNOT_ANSWER


def test_a_forecast_with_no_commitment_exits_zero():
    code, _ = run([*FAST, "forecast", "--history", "8 5 9 7 6", "--backlog", "50"])
    assert code == EXIT_SAFE


def test_the_json_flag_emits_parseable_json():
    code, out = run([*FAST, "--json", "forecast", "--history", "8 5 9 7 6",
                     "--backlog", "50", "--committed", "8"])
    payload = json.loads(out)
    assert "percentile_sprints" in payload
    assert code in (EXIT_SAFE, EXIT_UNSAFE)


def test_the_scenarios_command_summarises_the_fixture():
    code, out = run([*FAST, "scenarios"])
    assert code == EXIT_SAFE
    assert "below P50" in out


def test_the_scenarios_command_can_emit_json_with_the_headline_counts():
    code, out = run([*FAST, "--json", "scenarios"])
    payload = json.loads(out)
    assert payload["scenarios"] == 12
    assert "commitments_below_p50" in payload


def test_the_calibrate_command_emits_empirical_coverage_json():
    code, out = run([*FAST, "calibrate", "--teams", "150", "--history-len", "8"])
    payload = json.loads(out)
    assert "empirical" in payload
    assert payload["valid_teams"] > 0


def test_the_seed_and_confidence_flags_reach_the_config():
    # A lenient target makes a borderline commitment safe; a strict one makes it unsafe.
    safe, _ = run([*FAST, "--confidence", "0.3", "forecast", "--history", "8 5 9 7 6",
                   "--backlog", "50", "--committed", "8"])
    unsafe, _ = run([*FAST, "--confidence", "0.99", "forecast", "--history", "8 5 9 7 6",
                     "--backlog", "50", "--committed", "8"])
    assert safe == EXIT_SAFE
    assert unsafe == EXIT_UNSAFE


def test_the_scenarios_command_skips_a_degenerate_scenario_and_still_summarises(tmp_path):
    """A fixture row the forecaster cannot answer is reported to stderr and skipped,
    not allowed to abort the whole run."""
    import json as _json

    bad = {
        "scenarios": [
            {"name": "ok", "history": [8, 5, 9, 7, 6], "backlog": 50,
             "committed_sprints": 8, "sprint_days": 14, "start_date": "2026-01-06"},
            {"name": "degenerate", "history": [0, 0, 0, 0, 1], "backlog": 600,
             "committed_sprints": 10, "sprint_days": 14, "start_date": "2026-01-06"},
        ]
    }
    path = tmp_path / "s.json"
    path.write_text(_json.dumps(bad))
    code, out = run([*FAST, "--json", "scenarios", "--path", str(path)])
    payload = _json.loads(out)
    assert payload["scenarios"] == 1  # the degenerate one was skipped
    assert code == EXIT_SAFE


def test_missing_subcommand_is_a_usage_error():
    with pytest.raises(SystemExit):
        main([])
