#!/usr/bin/env python
"""Render the committed evidence charts with matplotlib, headless, no browser.

These PNGs are the repository's evidence because they come straight from the forecaster and
the experiment JSON and reproduce offline with one command. A browser screenshot of the HTML
report needs Chromium, which the build sandbox did not have (ADR-005); these charts need
nothing but matplotlib, so they are the evidence the README leads with.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
CHARTS = ROOT / "docs" / "charts"
EXP = ROOT / "docs" / "experiments"

from sprint_forecast.config import ForecastConfig  # noqa: E402
from sprint_forecast.forecast import forecast  # noqa: E402
from sprint_forecast.generator import load_scenarios  # noqa: E402

INK = "#1b4f72"
WARN = "#b0392f"
OK = "#1b7a3d"


def chart_distribution() -> Path:
    """One team's completion distribution, with its committed date marked against P50/P85.
    The committed date sits in the left tail, which is the whole point."""
    scenarios = load_scenarios(ROOT / "data" / "scenarios.json")
    sc = next(s for s in scenarios if s["name"] == "volatile-swings")
    fc = forecast(sc["history"], sc["backlog"], ForecastConfig(),
                  committed_sprints=sc["committed_sprints"])
    sprints = sorted(fc.histogram)
    counts = [fc.histogram[s] for s in sprints]

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(sprints, counts, color="#c9d6e5", edgecolor=INK, linewidth=0.6, label="trials")
    ax.axvline(fc.p50, color=INK, linestyle="--", linewidth=1.6,
               label=f"P50 = sprint {fc.p50}")
    ax.axvline(fc.percentile_sprints[85], color=OK, linestyle="--", linewidth=1.6,
               label=f"P85 = sprint {fc.percentile_sprints[85]}")
    ax.axvline(fc.committed_sprints, color=WARN, linewidth=2.2,
               label=f"committed = sprint {fc.committed_sprints} "
                     f"(P(meet) {fc.prob_meet_committed:.0%})")
    ax.set_title(f"Completion distribution: {sc['name']} "
                 f"({fc.trials} trials, backlog {int(fc.backlog)})")
    ax.set_xlabel("sprints to burn down the backlog")
    ax.set_ylabel("number of trials")
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    out = CHARTS / "distribution_volatile-swings.png"
    fig.savefig(out, dpi=130)
    plt.close(fig)
    return out


def chart_calibration() -> Path:
    """Nominal versus empirical coverage. Points under the diagonal are optimistic."""
    data = json.loads((EXP / "exp03_calibration.json").read_text())
    cov = data["empirical_coverage"]
    ps = sorted(int(p) for p in cov)
    nominal = [p / 100 for p in ps]
    empirical = [cov[str(p)] for p in ps]

    fig, ax = plt.subplots(figsize=(5.2, 5))
    ax.plot([0.4, 1.0], [0.4, 1.0], color="#888", linestyle=":", label="perfect calibration")
    ax.scatter(nominal, empirical, color=INK, zorder=3, s=50)
    for p, x, y in zip(ps, nominal, empirical, strict=True):
        ax.annotate(f"P{p}", (x, y), textcoords="offset points", xytext=(6, -10), fontsize=9)
    ax.set_title(f"Calibration on {data['valid_teams']} synthetic teams "
                 f"(history {data['history_len']} sprints)")
    ax.set_xlabel("nominal percentile")
    ax.set_ylabel("empirical coverage")
    ax.set_xlim(0.4, 1.0)
    ax.set_ylim(0.4, 1.0)
    ax.legend(frameon=False, fontsize=9, loc="upper left")
    fig.tight_layout()
    out = CHARTS / "calibration.png"
    fig.savefig(out, dpi=130)
    plt.close(fig)
    return out


def chart_sample_size() -> Path:
    """P95 coverage against history length: the tail closes as the history grows."""
    data = json.loads((EXP / "exp04_sample_size.json").read_text())
    recs = data["records"]
    lengths = [r["history_len"] for r in recs]
    p95 = [r["p95_coverage"] for r in recs]

    fig, ax = plt.subplots(figsize=(6.5, 4))
    ax.plot(lengths, p95, marker="o", color=INK, label="P95 empirical coverage")
    ax.axhline(0.95, color=WARN, linestyle="--", linewidth=1.2, label="nominal 0.95")
    ax.set_title("A short history under-covers the tail")
    ax.set_xlabel("sprints of history observed")
    ax.set_ylabel("P95 empirical coverage")
    ax.legend(frameon=False, fontsize=9)
    fig.tight_layout()
    out = CHARTS / "sample_size.png"
    fig.savefig(out, dpi=130)
    plt.close(fig)
    return out


def main() -> None:
    CHARTS.mkdir(parents=True, exist_ok=True)
    for fn in (chart_distribution, chart_calibration, chart_sample_size):
        path = fn()
        print(f"wrote {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
