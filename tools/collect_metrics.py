#!/usr/bin/env python
"""Re-measure every published figure and write docs/metrics.json. Nothing is typed by hand.

Test count and coverage come from the machine-readable pytest reports (junit XML and the
coverage JSON), not from a parsed progress line, because a parsed line quietly becomes
whatever the last run happened to print. The derived figures come from the experiment JSON
written by experiments/exp0*.py. The anchor phrases that guard each figure in prose are
defined here, next to the value, so a figure and its guard never drift apart.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "docs" / "experiments"
REPORTS = ROOT / "reports"
COVERAGE_JSON = ROOT / "coverage.json"


def _run_tests() -> None:
    REPORTS.mkdir(exist_ok=True)
    cmd = [
        sys.executable, "-m", "pytest",
        "--cov=sprint_forecast", "--cov-branch",
        "--cov-report=json:" + str(COVERAGE_JSON),
        "--junitxml=" + str(REPORTS / "junit.xml"),
    ]
    subprocess.run(cmd, cwd=ROOT, check=True)


def _tests_total() -> int:
    tree = ElementTree.parse(REPORTS / "junit.xml")
    root = tree.getroot()
    suites = root.findall("testsuite") or [root]
    return sum(int(s.get("tests", 0)) for s in suites)


def _line_coverage_pct() -> float:
    totals = json.loads(COVERAGE_JSON.read_text())["totals"]
    # Line coverage specifically: covered statements over total statements. Reported to one
    # decimal because the floor check compares against a single-decimal threshold.
    return round(100.0 * totals["covered_lines"] / totals["num_statements"], 1)


def _exp(name: str) -> dict:
    return json.loads((EXP / f"{name}.json").read_text())


def collect(skip_tests: bool) -> dict:
    if not skip_tests:
        _run_tests()
    if not (REPORTS / "junit.xml").exists() or not COVERAGE_JSON.exists():
        raise SystemExit("test reports missing; run `make test` or drop --skip-tests")

    e1 = _exp("exp01_commitment_honesty")
    e2 = _exp("exp02_p50_p85_gap")
    e3 = _exp("exp03_calibration")
    e4 = _exp("exp04_sample_size")
    e5 = _exp("exp05_degenerate")

    metrics = {
        "tests_total": _tests_total(),
        "coverage_line_pct": _line_coverage_pct(),
        "scenarios_total": e1["scenarios_total"],
        "commitments_below_p50": e1["commitments_below_p50"],
        "commitments_failing_target": e1["commitments_failing_target"],
        "max_gap_sprints": e2["max_p50_p85_gap_sprints"],
        "median_gap_sprints": e2["median_p50_p85_gap_sprints"],
        "p85_coverage_pct": e3["p85_empirical_coverage_pct"],
        "p95_coverage_pct": e3["p95_empirical_coverage_pct"],
        "tail_shortfall_points": e3["worst_shortfall_points"],
        "calibration_teams": e3["valid_teams"],
        "p95_coverage_short_pct": round(e4["p95_coverage_shortest"] * 100, 1),
        "p95_coverage_long_pct": round(e4["p95_coverage_longest"] * 100, 1),
        "degenerate_refused": e5["cases_refused"],
    }

    # Anchor phrases: short (two or three words) so they survive markdown line wrapping,
    # and alternatives because the same figure reads differently in a table and a sentence.
    anchors = {
        "tests_total": ["{} tests"],
        "coverage_line_pct": ["{}% line coverage", "{} percent line coverage"],
        "scenarios_total": ["{} scenarios", "{} synthetic teams"],
        "commitments_below_p50": ["{} of 12 committed", "{} of the twelve committed",
                                  "{} committed dates were below"],
        "commitments_failing_target": ["{} of 12 failed", "{} failed the"],
        "max_gap_sprints": ["up to {} sprints", "largest is {} sprints", "{}-sprint buffer"],
        "median_gap_sprints": ["median {} sprint", "median is {} sprint"],
        "p85_coverage_pct": ["P85 covered {}", "covered {}% of"],
        "p95_coverage_pct": ["P95 covered {}", "{}% in the tail"],
        "tail_shortfall_points": ["{} points", "{}-point"],
        "calibration_teams": ["{} synthetic teams", "on {} teams", "across {} teams"],
        "p95_coverage_short_pct": ["{}% at four", "from {}%"],
        "p95_coverage_long_pct": ["{}% at forty", "to {}%"],
        "degenerate_refused": ["{} of 4 degenerate", "{} of four degenerate"],
    }

    payload = {
        "metrics": metrics,
        "anchors": anchors,
        "checked_documents": ["README.md", "docs/defense-guide.md"],
        "note": "every value here is produced by running the suite and the experiments",
    }
    (ROOT / "docs" / "metrics.json").write_text(json.dumps(payload, indent=2) + "\n")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="re-measure every published figure")
    parser.add_argument("--skip-tests", action="store_true",
                        help="read existing reports instead of running pytest")
    args = parser.parse_args()
    payload = collect(args.skip_tests)
    print("wrote docs/metrics.json")
    for key, value in payload["metrics"].items():
        print(f"  {key} = {value}")


if __name__ == "__main__":
    main()
