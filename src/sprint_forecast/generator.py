"""Generate the committed scenario fixture: synthetic teams that behave like real ones.

Every number the README leads with comes from this fixture, so it is seeded and frozen
to data/scenarios.json rather than invented. The archetypes below are deliberately mixed
so the set contains optimistic commitments, stretch commitments and sandbagged ones: the
headline is only honest if the fixture was not stacked to produce it.

Nothing here is a fact about any real team or person. It is synthetic data, labelled as
such, and the generator is committed so a reviewer can regenerate the file byte for byte.
"""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np

from .calibration import negbinom_sampler

START_DATE = "2026-01-06"
SPRINT_DAYS = 14


@dataclass(frozen=True)
class Archetype:
    name: str
    description: str
    mean: float
    dispersion: float
    history_len: int
    backlog_mult: float  # backlog = round(mean * history_len * backlog_mult)
    commit_policy: str  # optimistic | stretch | buffered | sandbagged
    seed: int


# Twelve archetypes, ordered to interleave risky and safe commitments so the fixture is
# visibly not cherry-picked. commit_policy sets the committed date relative to the naive
# estimate, which is how an over-eager or a cautious plan actually gets made.
ARCHETYPES: tuple[Archetype, ...] = (
    Archetype("steady-core", "Low-variance team, honest stretch commit",
              8.0, 1.5, 10, 1.0, "stretch", 101),
    Archetype("volatile-swings", "High-variance team promising its best week",
              7.0, 3.0, 10, 1.0, "optimistic", 102),
    Archetype("fast-but-noisy", "Fast team, optimistic commit",
              12.0, 2.5, 8, 1.0, "optimistic", 103),
    Archetype("slow-steady", "Slow, consistent team with a buffer",
              4.0, 1.4, 12, 1.0, "buffered", 104),
    Archetype("short-history", "Only six sprints of data, stretch commit",
              9.0, 2.0, 6, 1.0, "stretch", 105),
    Archetype("holiday-gap", "A zero-throughput sprint in the history",
              6.0, 2.0, 10, 1.0, "stretch", 106),
    Archetype("sandbagged", "Cautious team that over-reserved",
              10.0, 1.6, 10, 1.0, "sandbagged", 107),
    Archetype("stretch-goal", "Aggressive commit on a wide backlog",
              8.0, 2.2, 10, 1.3, "optimistic", 108),
    Archetype("improving-team", "Recently faster, commit on the old pace",
              7.0, 1.8, 12, 1.0, "buffered", 109),
    Archetype("thin-margin", "Average team, coin-flip stretch",
              9.0, 2.0, 10, 1.1, "stretch", 110),
    Archetype("big-backlog", "Large backlog, buffered commit",
              11.0, 1.9, 10, 1.4, "buffered", 111),
    Archetype("tight-deadline", "Small backlog promised a sprint early",
              6.0, 2.0, 9, 0.7, "optimistic", 112),
)


def _history_for(arc: Archetype) -> list[int]:
    rng = np.random.default_rng(arc.seed)
    sampler = negbinom_sampler(mean=arc.mean, dispersion=arc.dispersion)
    values = [int(v) for v in sampler(rng, arc.history_len)]
    if arc.name == "holiday-gap":
        values[len(values) // 2] = 0  # force one zero sprint, a real two-week shutdown
    if all(v == 0 for v in values):  # pragma: no cover - guards an impossible NB draw
        values[0] = max(1, int(round(arc.mean)))
    return values


def _committed_sprints(history: list[int], backlog: int, policy: str) -> int:
    mean = sum(history) / len(history)
    naive = max(1, math.ceil(backlog / mean))
    offset = {"optimistic": -2, "stretch": 0, "buffered": 2, "sandbagged": 5}[policy]
    return max(1, naive + offset)


def build_scenarios() -> list[dict]:
    """Return the full scenario list, each a plain dict ready for JSON."""
    scenarios: list[dict] = []
    for arc in ARCHETYPES:
        history = _history_for(arc)
        backlog = int(round(arc.mean * arc.history_len * arc.backlog_mult))
        committed = _committed_sprints(history, backlog, arc.commit_policy)
        scenarios.append(
            {
                "name": arc.name,
                "description": arc.description,
                "commit_policy": arc.commit_policy,
                "history": history,
                "backlog": backlog,
                "committed_sprints": committed,
                "sprint_days": SPRINT_DAYS,
                "start_date": START_DATE,
            }
        )
    return scenarios


def write_scenarios(path: str | Path) -> Path:
    """Write the fixture to disk, sorted and indented so a diff is readable."""
    path = Path(path)
    payload = {
        "note": "synthetic seeded scenarios; regenerate with tools/regen_scenarios.py",
        "archetypes": [asdict(a) for a in ARCHETYPES],
        "scenarios": build_scenarios(),
    }
    path.write_text(json.dumps(payload, indent=2) + "\n")
    return path


def load_scenarios(path: str | Path) -> list[dict]:
    data = json.loads(Path(path).read_text())
    return data["scenarios"]
