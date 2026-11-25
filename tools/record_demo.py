#!/usr/bin/env python
"""Capture the demo commands' real output to a manifest and a transcript, no browser.

A screen recording would need Chromium, which the build sandbox did not have (ADR-005).
This is the honest substitute: run each demo command, capture its real stdout, exit code
and wall time, and commit them. A reviewer can replay the exact commands and get the exact
output, which is what the evidence is supposed to prove. Every line in the transcript is
captured, never hand written.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "video"

# Ordered as the argument, not as a feature list: the baseline unsafe date first, then the
# safe one, then the headline across the fixture, then the self-grading calibration, then
# the refusal on a degenerate team.
COMMANDS = [
    ["sprint-forecast", "forecast", "--history", "7 12 3 9 5 11 4 8 6 10",
     "--backlog", "70", "--committed", "7", "--name", "volatile-swings"],
    ["sprint-forecast", "forecast", "--history", "7 12 3 9 5 11 4 8 6 10",
     "--backlog", "70", "--committed", "11", "--name", "volatile-swings"],
    ["sprint-forecast", "scenarios"],
    ["sprint-forecast", "--trials", "2000", "calibrate", "--teams", "2000", "--history-len", "8"],
    ["sprint-forecast", "forecast", "--history", "0 0 0 0 1", "--backlog", "600"],
]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    # Warm the import once so the first timed command does not pay the startup cost.
    subprocess.run(["sprint-forecast", "--help"], cwd=ROOT, capture_output=True)

    segments = []
    transcript_lines = []
    for cmd in COMMANDS:
        start = time.perf_counter()
        proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        duration = time.perf_counter() - start
        output = proc.stdout + (proc.stderr or "")
        segments.append({
            "command": " ".join(cmd),
            "exit_code": proc.returncode,
            "duration_s": round(duration, 3),
            "stdout_lines": proc.stdout.count("\n"),
        })
        transcript_lines.append(f"$ {' '.join(cmd)}")
        transcript_lines.append(output.rstrip("\n"))
        transcript_lines.append(f"[exit {proc.returncode}]")
        transcript_lines.append("")

    (OUT / "manifest.json").write_text(json.dumps(
        {"note": "captured by tools/record_demo.py; every line is real output, no browser",
         "segments": segments}, indent=2) + "\n")
    (OUT / "transcript.txt").write_text("\n".join(transcript_lines))
    print(f"wrote {(OUT / 'manifest.json').relative_to(ROOT)} with {len(segments)} segments")
    for seg in segments:
        print(f"  exit {seg['exit_code']}  {seg['duration_s']:.2f}s  {seg['command'][:60]}")
    # The demo must exercise all three exit codes, or it is not demonstrating the contract.
    codes = {seg["exit_code"] for seg in segments}
    if not {0, 2, 3} <= codes:
        sys.exit(f"demo did not exercise all exit codes, saw {sorted(codes)}")


if __name__ == "__main__":
    main()
