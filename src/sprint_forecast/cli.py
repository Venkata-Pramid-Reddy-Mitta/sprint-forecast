"""Command line entry point, and the home of the exit-code contract.

The exit code is the interface a CI gate actually consumes, so it carries meaning:

    0  forecast produced and the committed date is SAFE (clears the confidence target),
       or a forecast was produced with no commitment to judge.
    2  forecast produced and the committed date is UNSAFE (the honest answer is "no").
    3  the tool could NOT answer: invalid input, or an unbounded forecast.

The 2 versus 3 split is the whole point (ADR-003): a delivery gate must treat "the date is
risky" and "we could not compute a date" differently, and a single non-zero code hides that.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .calibration import negbinom_sampler, run_coverage
from .config import ForecastConfig
from .errors import ForecastError
from .forecast import forecast
from .generator import load_scenarios
from .report import forecast_to_dict, render_text

EXIT_SAFE = 0
EXIT_UNSAFE = 2
EXIT_CANNOT_ANSWER = 3


def _parse_history(raw: str) -> list[float]:
    return [float(x) for x in raw.replace(",", " ").split()]


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sprint-forecast", description=__doc__.splitlines()[0])
    parser.add_argument("--trials", type=int, default=None, help="Monte Carlo sample size")
    parser.add_argument("--seed", type=int, default=None, help="override the RNG seed")
    parser.add_argument("--confidence", type=float, default=None, help="confidence target 0-1")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of text")
    sub = parser.add_subparsers(dest="command", required=True)

    f = sub.add_parser("forecast", help="forecast one team from throughput history")
    f.add_argument("--history", required=True, help="per-sprint throughput, comma or space sep")
    f.add_argument("--backlog", required=True, type=float, help="items remaining")
    f.add_argument("--committed", type=int, default=None, help="committed sprint count to judge")
    f.add_argument("--name", default="team", help="label for the report")
    f.add_argument("--start-date", default="2026-01-06", help="ISO start date for completion dates")
    f.add_argument("--sprint-days", type=int, default=14, help="calendar days per sprint")

    s = sub.add_parser("scenarios", help="forecast the committed fixture and summarise")
    s.add_argument("--path", default=None, help="path to scenarios.json")

    c = sub.add_parser("calibrate", help="measure empirical coverage on synthetic teams")
    c.add_argument("--history-len", type=int, default=8)
    c.add_argument("--teams", type=int, default=2000)
    c.add_argument("--backlog", type=float, default=64.0)
    return parser


def _config_from_args(args: argparse.Namespace) -> ForecastConfig:
    kwargs: dict = {}
    if args.trials is not None:
        kwargs["trials"] = args.trials
    if args.seed is not None:
        kwargs["seed"] = args.seed
    if args.confidence is not None:
        kwargs["confidence_target"] = args.confidence
    return ForecastConfig(**kwargs)


def _cmd_forecast(args: argparse.Namespace, cfg: ForecastConfig, out) -> int:
    try:
        fc = forecast(
            _parse_history(args.history),
            args.backlog,
            cfg,
            committed_sprints=args.committed,
        )
    except ForecastError as exc:
        print(f"cannot forecast: {exc}", file=sys.stderr)
        return EXIT_CANNOT_ANSWER
    if args.json:
        payload = forecast_to_dict(fc, args.name, args.start_date, args.sprint_days)
        print(json.dumps(payload, indent=2), file=out)
    else:
        print(render_text(fc, args.name, args.start_date, args.sprint_days), file=out)
    if fc.verdict == "unsafe":
        return EXIT_UNSAFE
    return EXIT_SAFE


def _cmd_scenarios(args: argparse.Namespace, cfg: ForecastConfig, out) -> int:
    path = args.path or (Path(__file__).resolve().parents[2] / "data" / "scenarios.json")
    scenarios = load_scenarios(path)
    below_p50 = 0
    unsafe = 0
    records = []
    for sc in scenarios:
        try:
            fc = forecast(
                sc["history"], sc["backlog"], cfg, committed_sprints=sc["committed_sprints"]
            )
        except ForecastError as exc:
            print(f"{sc['name']}: cannot forecast: {exc}", file=sys.stderr)
            continue
        below_p50 += 1 if fc.committed_below_p50 else 0
        unsafe += 1 if fc.verdict == "unsafe" else 0
        records.append(forecast_to_dict(fc, sc["name"], sc["start_date"], sc["sprint_days"]))
    summary = {
        "scenarios": len(records),
        "commitments_below_p50": below_p50,
        "commitments_failing_target": unsafe,
        "records": records,
    }
    if args.json:
        print(json.dumps(summary, indent=2), file=out)
    else:
        print(f"{len(records)} scenarios forecast", file=out)
        print(f"{below_p50} committed dates were below P50 (a coin flip or worse)", file=out)
        print(f"{unsafe} did not clear the {cfg.confidence_target:.0%} target", file=out)
    # A fixture summary is informational; it always succeeds if it ran.
    return EXIT_SAFE


def _cmd_calibrate(args: argparse.Namespace, cfg: ForecastConfig, out) -> int:
    result = run_coverage(
        negbinom_sampler(),
        history_len=args.history_len,
        n_teams=args.teams,
        backlog=args.backlog,
        config=cfg,
    )
    payload = {
        "history_len": result.history_len,
        "valid_teams": result.valid_teams,
        "nominal": result.nominal,
        "empirical": {str(p): round(v, 4) for p, v in result.empirical.items()},
        "resolution_floor": round(result.resolution_floor, 5),
    }
    print(json.dumps(payload, indent=2), file=out)
    return EXIT_SAFE


def main(argv: list[str] | None = None, out=None) -> int:
    out = out or sys.stdout
    args = _build_parser().parse_args(argv)
    cfg = _config_from_args(args)
    if args.command == "forecast":
        return _cmd_forecast(args, cfg, out)
    if args.command == "scenarios":
        return _cmd_scenarios(args, cfg, out)
    if args.command == "calibrate":
        return _cmd_calibrate(args, cfg, out)
    raise AssertionError(f"unhandled command {args.command}")  # pragma: no cover


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
