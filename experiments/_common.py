"""Shared plumbing for the experiments: locate the repo, write JSON, print a table.

Kept tiny and dependency-free so each experiment file stays readable as the answer to
one question. Every experiment writes its result to docs/experiments/<name>.json, which
tools/collect_metrics.py then reads; nothing downstream parses a printed line.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
EXPERIMENTS_DIR = ROOT / "docs" / "experiments"


def write_result(name: str, payload: dict) -> Path:
    EXPERIMENTS_DIR.mkdir(parents=True, exist_ok=True)
    path = EXPERIMENTS_DIR / f"{name}.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return path


def print_table(headers: list[str], rows: list[list[object]]) -> None:
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(str(cell)))
    line = "  ".join(h.ljust(widths[i]) for i, h in enumerate(headers))
    print(line)
    print("  ".join("-" * widths[i] for i in range(len(headers))))
    for row in rows:
        print("  ".join(str(c).ljust(widths[i]) for i, c in enumerate(row)))
