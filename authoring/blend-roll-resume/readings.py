"""The contract tools/readingcheck.py reads: every wrong reading, and how to run one.

The readings themselves are built by make_readings.py, which patches the reference and asserts
that every patch fired. This file only points at them, so the two cannot drift.
"""
import importlib
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
TASK = HERE.parents[1] / "tasks" / "blend-roll-resume"
REFERENCE = str(TASK / "solution")
SRC = TASK / "environment" / "app_src"
PARTS = ("deck.py", "pick.py", "walk.py", "lay.py", "keep.py", "turn.py")

sys.path.insert(0, str(TASK / "tests"))
import cases  # noqa: E402
import gen  # noqa: E402

# These two read the rules exactly right and differ from the reference only in what they cost,
# so no enumerated script can separate them and none is claimed to. They are ruled out by the
# clock on the worker, which the Tolerances table of trace.md carries, and they ship as cheats
# like every other reading.
TIMING = ("slow-per-draw", "slow-per-step")

READINGS = {
    d.name: {p.name: p.read_text(encoding="utf-8") for p in sorted(d.glob("*.py"))}
    for d in sorted((HERE / "readings").iterdir())
    if d.is_dir() and d.name not in TIMING
}

# The same names as a literal table, so tools/tracecheck.py can read them without importing
# this file. The assertion below is what stops the two drifting apart.
EDITS = {
    "at-departed": "a departed source still reports an epoch and a cursor",
    "cap-early": "a capped source leaves as its last permitted epoch begins",
    "cap-late": "a capped source serves one epoch past its cap",
    "depart-step-end": "a departure takes effect when the step it fell in is over",
    "done-next-draw": "a done line carries the draw after the one that took the last sample",
    "feed-announces": "a feed announces a departure it only looked at",
    "feed-commits": "a feed takes the draws it reports",
    "feed-own-slot": "a feed settles only its own micro-batch, not the draws before it",
    "join-reset": "a stop puts back every source, the ones it never saw included",
    "keep-blend": "a stop puts the blend back along with the run",
    "lay-contig": "each rank takes one contiguous block of the step",
    "lay-no-accum": "the accumulation depth does not widen a step",
    "no-rebase-drop": "a departure leaves the remaining counters where they are",
    "no-rebase-join": "declaring a source mid-run leaves the counters where they are",
    "no-rebase-weigh": "a reweighing leaves the counters where they are",
    "rebase-always": "a restart always starts a fresh segment",
    "rebase-by-sum": "the blend counts as unchanged while the live count and weight total hold",
    "rebase-never": "the counters a stop puts back always stand",
    "tie-late": "a tie in the draw rule goes to the later declared source",
    "tie-weight": "a tie in the draw rule goes to the heavier source",
    "total-counter": "the draw rule reads whole consumption, not draws since the blend changed",
}

assert set(EDITS) == set(READINGS), sorted(set(EDITS) ^ set(READINGS))


def run(policy, text):
    """Drive one script under one directory of editable files."""
    room = Path(tempfile.mkdtemp(prefix="brr-run-"))
    here = room / "app"
    shutil.copytree(SRC, here, ignore=shutil.ignore_patterns("__pycache__"))
    for part in PARTS:
        one = Path(policy) / part
        if one.is_file():
            shutil.copy(one, here / "mix" / part)
    sys.path.insert(0, str(here))
    for mod in [m for m in list(sys.modules) if m == "ops" or m.startswith("mix")]:
        del sys.modules[mod]
    try:
        ops = importlib.import_module("ops")
        hold = importlib.import_module("mix.hold")
        h = hold.Hold()
        for line in text.strip().splitlines():
            if line.strip():
                ops.ex(h, tuple(line.split()))
        return list(h.out)
    finally:
        sys.path.remove(str(here))
        shutil.rmtree(room, ignore_errors=True)


def enumerated():
    return [(name, "\n".join(cases.ops(name))) for name in cases.ORDER]


def generated(n):
    out = []
    for fam, name, lines in gen.programs("readingcheck", max(1, n // 8)):
        if fam == "big":
            continue
        out.append((name, "\n".join(lines)))
    return out[:n]


def reductions(text):
    """Structure-aware shrinking: a script stays legal only if its header survives."""
    lines = text.split("\n")
    head = [i for i, ln in enumerate(lines)
            if ln.split()[:1] and ln.split()[0] in ("seed", "src")]
    for i in range(len(lines) - 1, -1, -1):
        if i in head:
            continue
        yield "\n".join(lines[:i] + lines[i + 1:])
