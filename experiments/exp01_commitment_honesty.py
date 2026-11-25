#!/usr/bin/env python
"""Q: across a mixed set of teams, how many committed dates were a coin flip or worse?

This is the headline. Each scenario's committed date is priced against that team's own
throughput distribution, and we count how many landed below P50 (less likely than not)
and how many failed the 85 percent confidence target.
"""

from __future__ import annotations

from _common import ROOT, print_table, write_result
from sprint_forecast.config import ForecastConfig
from sprint_forecast.forecast import forecast
from sprint_forecast.generator import load_scenarios


def main() -> None:
    cfg = ForecastConfig()
    scenarios = load_scenarios(ROOT / "data" / "scenarios.json")
    rows = []
    below_p50 = 0
    failing = 0
    records = []
    for sc in scenarios:
        fc = forecast(sc["history"], sc["backlog"], cfg, committed_sprints=sc["committed_sprints"])
        below = bool(fc.committed_below_p50)
        below_p50 += 1 if below else 0
        failing += 1 if fc.verdict == "unsafe" else 0
        records.append(
            {
                "name": sc["name"],
                "committed_sprints": fc.committed_sprints,
                "p50": fc.p50,
                "p85": fc.percentile_sprints[85],
                "prob_meet": round(fc.prob_meet_committed, 4),
                "verdict": fc.verdict,
                "below_p50": below,
            }
        )
        rows.append([sc["name"], fc.committed_sprints, fc.p50, fc.percentile_sprints[85],
                     f"{fc.prob_meet_committed:.0%}", fc.verdict])

    payload = {
        "question": "how many committed dates were below P50 or failed the 85% target",
        "scenarios_total": len(scenarios),
        "commitments_below_p50": below_p50,
        "commitments_failing_target": failing,
        "confidence_target": cfg.confidence_target,
        "records": records,
    }
    write_result("exp01_commitment_honesty", payload)
    print_table(["scenario", "commit", "P50", "P85", "P(meet)", "verdict"], rows)
    print(
        f"\n{below_p50} of {len(scenarios)} committed dates were below P50; "
        f"{failing} of {len(scenarios)} failed the {cfg.confidence_target:.0%} target."
    )


if __name__ == "__main__":
    main()
