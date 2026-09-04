"""The wrong readings of the rule, so tools/readingcheck.py can ask whether the written set
separates each of them.

Per-rule coverage on paper is not coverage. The question is whether a *specific*
plausible-but-wrong reading survives the whole written set, and the only way to know is to
write the reading down and run it. Each entry here is the reference with one decision made the
way somebody who missed one piece would make it - the same swaps authoring/emit.py ships as
cheats, read back from authoring/cheatsrc/ so the two cannot drift apart.

`run` drives one task set under one policy and returns the graded fields, which is what the
verifier compares.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

TASK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TASK / "tests"))
sys.path.insert(0, str(TASK / "authoring"))

import oracle  # noqa: E402
import probe_case  # noqa: E402
import scen  # noqa: E402

REFERENCE = TASK / "solution"

FIELDS = ("trace", "prio", "ev", "done", "ids", "ticks")

# Every single-mistake cheat is a reading. The isolation probes and the memorisation attack are
# not: they are attacks on the reward channel rather than misreadings of the rule.
NOT_A_READING = {
    "hand-back-the-schedule", "replay-the-tables", "peek-at-the-scenarios", "plant-and-exit",
    "plant-the-report", "probe-privileges", "read-the-answers", "reward-daemon",
    "rewrite-the-scheduler", "sweep-the-image",
}


def _readings():
    out = {}
    for d in sorted((TASK / "authoring" / "cheatsrc").iterdir()):
        if not d.is_dir() or d.name in NOT_A_READING:
            continue
        src = d / "prio.py"
        if src.is_file():
            out[d.name] = {"prio.py": src.read_text()}
    return out


READINGS = _readings()


def run(policy, text):
    """Drive one task set under one policy directory and return the graded fields."""
    sc = json.loads(text)
    got = probe_case.drive(Path(policy) / "prio.py", sc)
    if "err" in got:
        return ("raised", got["err"][:200])
    return tuple(json.dumps(got[f], sort_keys=True) for f in FIELDS)


def enumerated():
    return [(sc["name"], json.dumps(sc)) for sc in scen.SCENARIOS]


def generated(n):
    sets = scen.batch(scen.seed_from("readingcheck"), n)
    return [(sc["name"], json.dumps(sc)) for sc in sets]
