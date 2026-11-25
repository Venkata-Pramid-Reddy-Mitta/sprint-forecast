#!/usr/bin/env python
"""Fail the build if line coverage drops below a floor. Reads coverage.xml, not a progress
line, so the floor is enforced against the same number the report shows."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]


def line_coverage_pct() -> float:
    root = ElementTree.parse(ROOT / "coverage.xml").getroot()
    return float(root.get("line-rate", "0")) * 100.0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--min", type=float, default=95.0)
    args = parser.parse_args()
    pct = line_coverage_pct()
    print(f"line coverage {pct:.1f}% (floor {args.min:.1f}%)")
    if pct + 1e-9 < args.min:
        sys.exit(f"coverage {pct:.1f}% is below the floor {args.min:.1f}%")


if __name__ == "__main__":
    main()
