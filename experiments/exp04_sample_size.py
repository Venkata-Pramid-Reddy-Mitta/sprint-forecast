#!/usr/bin/env python
"""Q: when is a team's history too short to commit on?

Sweep the number of observed sprints and watch two things move: the empirical coverage of
the P85 and P95 (how honest the percentiles are) and the mean P50-to-P85 gap (how wide the
forecast has to be). Short histories under-cover the tail and force a wider buffer; the
point where coverage settles is the point where the history is long enough to trust.
"""

from __future__ import annotations

from _common import print_table, write_result
from sprint_forecast.calibration import negbinom_sampler, run_coverage
from sprint_forecast.config import ForecastConfig

LENGTHS = [4, 6, 8, 12, 20, 40]
N_TEAMS = 1500
BACKLOG = 64.0
CFG = ForecastConfig(trials=2000)


def main() -> None:
    sampler = negbinom_sampler(mean=8.0, dispersion=2.0)
    rows = []
    records = []
    for h in LENGTHS:
        r = run_coverage(sampler, history_len=h, n_teams=N_TEAMS, backlog=BACKLOG, config=CFG)
        rows.append([h, f"{r.empirical[85]:.3f}", f"{r.empirical[95]:.3f}",
                     f"{r.mean_gap_p50_p85_sprints:.2f}"])
        records.append({
            "history_len": h,
            "p85_coverage": round(r.empirical[85], 4),
            "p95_coverage": round(r.empirical[95], 4),
            "mean_gap_p50_p85_sprints": round(r.mean_gap_p50_p85_sprints, 3),
        })

    shortest = records[0]
    longest = records[-1]
    payload = {
        "question": "how coverage and forecast width change with history length",
        "n_teams": N_TEAMS,
        "lengths": LENGTHS,
        "records": records,
        "p95_coverage_shortest": shortest["p95_coverage"],
        "p95_coverage_longest": longest["p95_coverage"],
    }
    write_result("exp04_sample_size", payload)
    print_table(["history_len", "P85_cover", "P95_cover", "mean_gap"], rows)
    print(
        f"\nP95 coverage rises from {shortest['p95_coverage']:.1%} at "
        f"{shortest['history_len']} sprints to {longest['p95_coverage']:.1%} at "
        f"{longest['history_len']} sprints."
    )


if __name__ == "__main__":
    main()
