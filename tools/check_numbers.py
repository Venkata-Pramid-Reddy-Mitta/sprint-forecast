#!/usr/bin/env python
"""Fail the build when a document quotes a figure the code no longer produces.

The forward check is the one that fails the build: wherever a checked document uses an
anchor phrase, the number inside it must equal the freshly measured metric. The reverse
check is advisory: it lists numbers in prose that no metric guards, so a figure never
slips in unmeasured, but it does not fail the build because an example row of data is
allowed to contain a made-up number.

Code is excluded before matching: fenced blocks and inline spans, because an example
invocation with a round count is legitimate and flagging it teaches a reader to ignore
the section (receipts rule, learned the hard way).
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
METRICS = ROOT / "docs" / "metrics.json"

NUMBER = re.compile(r"\d+(?:\.\d+)?")
# Numbers that are structural, not measured: years, version, the percentile labels, the
# confidence target, sprint length, and small list ordinals. They are allowed in prose.
ALLOWED = {
    "2026", "2026-01-06", "0.3.0", "0", "2", "3", "50", "70", "85", "95",
    "14", "100", "10000", "2000", "1500", "4", "6", "8", "12", "20", "40", "64",
    "1", "5", "0.85", "0.5",
}


def strip_code(text: str) -> str:
    text = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)
    text = re.sub(r"`[^`]*`", " ", text)
    return text


def _anchor_regex(template: str) -> re.Pattern:
    # Turn "P85 covered {}" into a regex that captures the number and tolerates the
    # whitespace a line wrap introduces between words.
    parts = template.split("{}")
    escaped = [re.escape(p).replace(r"\ ", r"\s+") for p in parts]
    return re.compile(r"(\d+(?:\.\d+)?)".join(escaped))


def _as_number(value: object) -> float:
    return float(value)


def check(verbose: bool = True) -> int:
    data = json.loads(METRICS.read_text())
    metrics = data["metrics"]
    anchors = data["anchors"]
    failures: list[str] = []
    confirmed = 0
    confirmed_spans: dict[str, list[tuple[int, int]]] = {}

    for doc_rel in data["checked_documents"]:
        doc_path = ROOT / doc_rel
        if not doc_path.exists():
            failures.append(f"{doc_rel}: checked document is missing")
            continue
        prose = strip_code(doc_path.read_text())
        confirmed_spans[doc_rel] = []
        for metric, templates in anchors.items():
            expected = _as_number(metrics[metric])
            for template in templates:
                for m in _anchor_regex(template).finditer(prose):
                    found = float(m.group(1))
                    if abs(found - expected) > 1e-6:
                        failures.append(
                            f"{doc_rel}: '{template.format(found)}' but {metric} = "
                            f"{metrics[metric]} (anchor '{template}')"
                        )
                    else:
                        confirmed += 1
                        confirmed_spans[doc_rel].append(m.span())

    # Reverse check: prose numbers not inside a confirmed anchor span and not allowed.
    unguarded: list[str] = []
    for doc_rel in data["checked_documents"]:
        doc_path = ROOT / doc_rel
        if not doc_path.exists():
            continue
        prose = strip_code(doc_path.read_text())
        spans = confirmed_spans.get(doc_rel, [])
        for m in NUMBER.finditer(prose):
            if any(s <= m.start() and m.end() <= e for s, e in spans):
                continue
            if m.group(0) in ALLOWED:
                continue
            context = prose[max(0, m.start() - 25): m.end() + 10].replace("\n", " ").strip()
            unguarded.append(f"{doc_rel}: unguarded number {m.group(0)!r} near '...{context}...'")

    if verbose:
        n_docs = len(data["checked_documents"])
        print(f"confirmed {confirmed} anchored figures across {n_docs} docs")
        for u in unguarded:
            print(f"  note: {u}")
    if failures:
        print("\nFAILED: documents disagree with measured metrics")
        for f in failures:
            print(f"  {f}")
        return 1
    print("OK: every anchored figure matches the measured metrics")
    return 0


if __name__ == "__main__":
    sys.exit(check())
