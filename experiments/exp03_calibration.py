#!/usr/bin/env python
"""Q: does a P85 date actually get hit 85 percent of the time?

The one experiment that grades the forecaster instead of running it. Build 2000 synthetic
teams from a known overdispersed distribution, forecast each from eight observed sprints,
draw a fresh true future, and measure how often reality landed at or under each predicted
percentile. The gap between nominal and empirical is the number that decides whether the
percentiles can be trusted.
"""

from __future__ import annotations

from _common import print_table, write_result
from sprint_forecast.calibration import negbinom_sampler, run_coverage
from sprint_forecast.config import ForecastConfig

HISTORY_LEN = 8
N_TEAMS = 2000
BACKLOG = 64.0
# A smaller trial count than the default, because calibration runs one forecast per team.
# The percentiles are integers, so 2000 trials place them stably (confirmed by exp04).
CFG = ForecastConfig(trials=2000)


def main() -> None:
    result = run_coverage(negbinom_sampler(mean=8.0, dispersion=2.0),
                          history_len=HISTORY_LEN, n_teams=N_TEAMS, backlog=BACKLOG, config=CFG)
    rows = []
    records = {}
    for p in CFG.percentiles:
        nominal = result.nominal[p]
        empirical = result.empirical[p]
        rows.append([f"P{p}", f"{nominal:.2f}", f"{empirical:.3f}",
                     f"{(empirical - nominal) * 100:+.1f}"])
        records[str(p)] = round(empirical, 4)

    worst_p, worst_points = result.worst_gap()
    payload = {
        "question": "empirical coverage of each nominal percentile on synthetic teams",
        "history_len": HISTORY_LEN,
        "valid_teams": result.valid_teams,
        "resolution_floor": round(result.resolution_floor, 5),
        "empirical_coverage": records,
        "p85_empirical_coverage_pct": round(result.empirical[85] * 100, 1),
        "p95_empirical_coverage_pct": round(result.empirical[95] * 100, 1),
        "worst_undercovered_percentile": worst_p,
        "worst_shortfall_points": round(worst_points, 1),
    }
    write_result("exp03_calibration", payload)
    print_table(["percentile", "nominal", "empirical", "gap_pts"], rows)
    print(
        f"\nOn {result.valid_teams} teams (resolution floor {result.resolution_floor:.4f}): "
        f"P85 covered {result.empirical[85]:.1%}, P95 covered {result.empirical[95]:.1%}. "
        f"The tail is optimistic because the bootstrap cannot resample an unseen value."
    )


if __name__ == "__main__":
    main()
