#!/usr/bin/env python
"""Regenerate data/scenarios.json from the seeded generator. Committed so a reviewer can
reproduce the fixture byte for byte and confirm it was not hand-tuned."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sprint_forecast.generator import write_scenarios  # noqa: E402

if __name__ == "__main__":
    out = write_scenarios(ROOT / "data" / "scenarios.json")
    print(f"wrote {out.relative_to(ROOT)}")
