#!/usr/bin/env python
"""Q: what does the tool do when there is no honest date to give?

A forecaster that always prints a date is worse than useless on a stalled team. Here we
feed the three degenerate inputs and record that each is refused with the right outcome
category rather than answered with a fabricated date: invalid input and an unreachable
backlog both map to "cannot answer" (exit 3), which is distinct from a valid but unsafe
forecast (exit 2).
"""

from __future__ import annotations

from _common import print_table, write_result
from sprint_forecast.config import ForecastConfig
from sprint_forecast.errors import InvalidInput, UnboundedForecast
from sprint_forecast.forecast import forecast

CFG = ForecastConfig()


def classify(history, backlog) -> tuple[str, str]:
    try:
        forecast(history, backlog, CFG)
        return ("forecast produced", "0 or 2")
    except InvalidInput:
        return ("refused: invalid input", "3")
    except UnboundedForecast:
        return ("refused: unbounded", "3")


def main() -> None:
    cases = [
        ("all-zero history", [0, 0, 0, 0], 40),
        ("unreachable backlog", [0, 0, 0, 0, 1], 600),
        ("empty history", [], 40),
        ("healthy team (control)", [8, 5, 9, 7, 6], 50),
    ]
    rows = []
    records = []
    refused = 0
    for name, history, backlog in cases:
        outcome, exit_cat = classify(history, backlog)
        if outcome.startswith("refused"):
            refused += 1
        rows.append([name, outcome, exit_cat])
        records.append({"case": name, "outcome": outcome, "exit_code": exit_cat})

    payload = {
        "question": "degenerate inputs are refused, not given a fabricated date",
        "cases_total": len(cases),
        "cases_refused": refused,
        "records": records,
    }
    write_result("exp05_degenerate", payload)
    print_table(["case", "outcome", "exit"], rows)
    print(f"\n{refused} of {len(cases)} inputs were refused with exit 3 (cannot answer).")


if __name__ == "__main__":
    main()
