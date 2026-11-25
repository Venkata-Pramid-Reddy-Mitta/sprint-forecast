#!/usr/bin/env python
"""Q: how big is the buffer between a coin-flip date and a safe date, and who budgets it?

The P50 date is where a team finishes half the time. The P85 date is where it finishes
most of the time. The gap between them is the schedule risk that a single committed date
hides entirely. We report that gap per team in sprints and the median across the set.
"""

from __future__ import annotations

import statistics

from _common import ROOT, print_table, write_result
from sprint_forecast.config import ForecastConfig
from sprint_forecast.forecast import forecast
from sprint_forecast.generator import load_scenarios


def main() -> None:
    cfg = ForecastConfig()
    scenarios = load_scenarios(ROOT / "data" / "scenarios.json")
    gaps_sprints = []
    rows = []
    records = []
    for sc in scenarios:
        fc = forecast(sc["history"], sc["backlog"], cfg)
        p50, p85 = fc.p50, fc.percentile_sprints[85]
        gap = p85 - p50
        gaps_sprints.append(gap)
        gap_days = gap * sc["sprint_days"]
        records.append({"name": sc["name"], "p50": p50, "p85": p85,
                        "gap_sprints": gap, "gap_days": gap_days})
        rows.append([sc["name"], p50, p85, gap, gap_days])

    median_gap = int(statistics.median(gaps_sprints))
    max_gap = max(gaps_sprints)
    payload = {
        "question": "the P50-to-P85 schedule buffer that a single date hides",
        "scenarios_total": len(scenarios),
        "median_p50_p85_gap_sprints": median_gap,
        "max_p50_p85_gap_sprints": max_gap,
        "sprint_days": cfg.sprint_days,
        "records": records,
    }
    write_result("exp02_p50_p85_gap", payload)
    print_table(["scenario", "P50", "P85", "gap_sprints", "gap_days"], rows)
    print(
        f"\nmedian P50-to-P85 gap: {median_gap} sprints; "
        f"largest: {max_gap} sprints. That buffer is absent from a single committed date."
    )


if __name__ == "__main__":
    main()
