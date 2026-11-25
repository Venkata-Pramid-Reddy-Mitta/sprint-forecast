"""Turn a Forecast into words, a table, dates, and a self-contained HTML report.

Dates live here, not in the engine, because a date is a presentation of a sprint count
against a start date and a sprint length. The engine stays in machine-independent sprint
counts (ADR-002); this layer is where a count becomes "week of 2 March".
"""

from __future__ import annotations

from datetime import date, timedelta

from .forecast import Forecast

# The CSS classes the HTML markup uses. A test asserts every one has a rule in STYLE, which
# is how an earlier project caught a badge rendering green text on a green cell.
BADGE_CLASSES = ("badge", "badge-safe", "badge-unsafe", "badge-none")

STYLE = """
body { font: 14px system-ui, sans-serif; color: #111; background: #fff; margin: 2rem; }
h1 { font-size: 20px; } h2 { font-size: 16px; margin-top: 1.5rem; }
table { border-collapse: collapse; margin: 0.5rem 0; }
th, td { border: 1px solid #ccc; padding: 4px 10px; text-align: right; }
th:first-child, td:first-child { text-align: left; }
.badge { display: inline-block; padding: 2px 10px; border-radius: 4px;
         font-weight: 700; color: #fff; }
.badge-safe { background: #1b7a3d; }
.badge-unsafe { background: #b0392f; }
.badge-none { background: #555; }
"""


def completion_date(start: str, sprints: int, sprint_days: int) -> str:
    """The calendar date a given sprint count lands on, as an ISO string."""
    start_date = date.fromisoformat(start)
    return (start_date + timedelta(days=sprints * sprint_days)).isoformat()


def forecast_to_dict(
    fc: Forecast,
    name: str,
    start_date: str,
    sprint_days: int,
) -> dict:
    """A fully serialisable view of a forecast, percentile dates included."""
    pct_dates = {
        p: (completion_date(start_date, s, sprint_days) if s is not None else None)
        for p, s in fc.percentile_sprints.items()
    }
    committed_date = (
        completion_date(start_date, fc.committed_sprints, sprint_days)
        if fc.committed_sprints is not None
        else None
    )
    return {
        "name": name,
        "n_history": fc.n_history,
        "mean_throughput": round(fc.mean_throughput, 3),
        "backlog": fc.backlog,
        "trials": fc.trials,
        "naive_sprints": fc.naive_sprints,
        "percentile_sprints": {str(p): s for p, s in fc.percentile_sprints.items()},
        "percentile_dates": {str(p): d for p, d in pct_dates.items()},
        "committed_sprints": fc.committed_sprints,
        "committed_date": committed_date,
        "prob_meet_committed": (
            round(fc.prob_meet_committed, 4) if fc.prob_meet_committed is not None else None
        ),
        "verdict": fc.verdict,
        "committed_below_p50": fc.committed_below_p50,
        "confidence_target": fc.confidence_target,
    }


def render_text(fc: Forecast, name: str, start_date: str, sprint_days: int) -> str:
    """The CLI's human-readable block. Leads with the percentile table, then the verdict."""
    lines = [f"Forecast: {name}"]
    lines.append(
        f"  history: {fc.n_history} sprints, mean {fc.mean_throughput:.2f} items/sprint, "
        f"backlog {fc.backlog:.0f} items, {fc.trials} trials"
    )
    lines.append("  percentile   sprints   completion")
    for p, s in fc.percentile_sprints.items():
        if s is None:
            lines.append(f"    P{p:<8d} unbounded  (not reached within cap)")
        else:
            d = completion_date(start_date, s, sprint_days)
            lines.append(f"    P{p:<8d} {s:>7d}   {d}")
    if fc.committed_sprints is not None and fc.prob_meet_committed is not None:
        cd = completion_date(start_date, fc.committed_sprints, sprint_days)
        lines.append(
            f"  committed: sprint {fc.committed_sprints} ({cd}), "
            f"probability of meeting it {fc.prob_meet_committed:.0%}"
        )
        verdict = fc.verdict.upper() if fc.verdict else "N/A"
        tag = "" if not fc.committed_below_p50 else "  [below P50: a coin flip or worse]"
        lines.append(
            f"  verdict: {verdict} at a {fc.confidence_target:.0%} confidence target{tag}"
        )
    return "\n".join(lines)


def _badge(fc: Forecast) -> str:
    verdict = fc.verdict
    if verdict is None:
        return '<span class="badge badge-none">NO COMMIT</span>'
    cls = "badge-safe" if verdict == "safe" else "badge-unsafe"
    return f'<span class="badge {cls}">{verdict.upper()}</span>'


def render_html(
    records: list[tuple[Forecast, str, str, int]],
    title: str = "Sprint forecast",
) -> str:
    """A self-contained HTML report over several forecasts. One row per scenario, the
    verdict badge in its own column. Used for the optional screenshot path; the committed
    evidence is the matplotlib charts, which need no browser (ADR-005)."""
    rows = []
    for fc, name, start_date, sprint_days in records:
        p50 = fc.percentile_sprints.get(50)
        p85 = fc.percentile_sprints.get(85)
        pm = f"{fc.prob_meet_committed:.0%}" if fc.prob_meet_committed is not None else "n/a"
        commit_cell = "-"
        if fc.committed_sprints is not None:
            cdate = completion_date(start_date, fc.committed_sprints, sprint_days)
            commit_cell = f"{fc.committed_sprints} ({cdate})"
        rows.append(
            "<tr>"
            f"<td>{name}</td><td>{fc.n_history}</td><td>{fc.backlog:.0f}</td>"
            f"<td>{p50 if p50 is not None else 'unbounded'}</td>"
            f"<td>{p85 if p85 is not None else 'unbounded'}</td>"
            f"<td>{commit_cell}</td>"
            f"<td>{pm}</td><td>{_badge(fc)}</td>"
            "</tr>"
        )
    header = (
        "<tr><th>scenario</th><th>history</th><th>backlog</th><th>P50</th>"
        "<th>P85</th><th>commit (date)</th><th>P(meet)</th><th>verdict</th></tr>"
    )
    return (
        "<!doctype html><html lang='en'><head><meta charset='utf-8'>"
        f"<title>{title}</title><style>{STYLE}</style></head><body>"
        f"<h1>{title}</h1>"
        "<p>Each committed date is priced against the team's own throughput distribution. "
        "A verdict of UNSAFE means the committed date did not clear the confidence target.</p>"
        f"<table>{header}{''.join(rows)}</table>"
        "</body></html>"
    )
