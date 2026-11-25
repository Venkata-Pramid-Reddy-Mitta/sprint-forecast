#!/usr/bin/env python
"""Write the uncomfortable table to the CI job summary, because that is where a human reads
it. Prints markdown to stdout; the workflow redirects it into $GITHUB_STEP_SUMMARY."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    m = json.loads((ROOT / "docs" / "metrics.json").read_text())["metrics"]
    print("## sprint-forecast: the numbers it would rather not publish\n")
    print("| figure | value |")
    print("|---|---|")
    print(f"| committed dates below P50 | {m['commitments_below_p50']} of {m['scenarios_total']} |")
    print(f"| commitments failing the 85% target | {m['commitments_failing_target']} of "
          f"{m['scenarios_total']} |")
    print(f"| P85 empirical coverage (nominal 85) | {m['p85_coverage_pct']}% |")
    print(f"| P95 empirical coverage (nominal 95) | {m['p95_coverage_pct']}% |")
    print(f"| tail optimism | {m['tail_shortfall_points']} points |")
    print(f"| tests / line coverage | {m['tests_total']} / {m['coverage_line_pct']}% |")
    print(f"\nMeasured on {m['calibration_teams']} synthetic teams. "
          "Every figure is re-measured by this job and checked against the docs.")


if __name__ == "__main__":
    main()
