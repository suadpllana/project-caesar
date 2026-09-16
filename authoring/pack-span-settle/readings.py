"""Does the enumerated set separate the wrong readings a solver will actually have?

Per-rule coverage on paper is not coverage. The question a hand-written case set cannot answer
by inspection is whether a specific plausible-but-wrong reading survives it, and the only way to
know is to write the reading down and run it.

The readings come from `emit.py`, so the cheats that ship and the readings measured here are the
same files and cannot drift apart. The slow families, the forgery and the isolation probes are
not readings of the rules and are not measured here.

    python tools/readingcheck.py pack-span-settle [rounds]
"""
import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import emit  # noqa: E402
import lab  # noqa: E402

sys.path.insert(0, str(lab.TASK / "tests"))
import cases  # noqa: E402
import gen  # noqa: E402

REFERENCE = str(lab.TASK / "solution")

# Stated literally so tools/tracecheck.py has a name to demand a row for, and asserted
# against what emit.py actually built so the two cannot drift apart.
EDITS = [
    "cross-score", "cut-always-back", "cut-brim", "cut-floor-one", "div-all-steps",
    "div-first-step", "div-length", "drop-late", "first-at-op", "floor-now", "floor-strict",
    "frac-raw", "lay-one-token", "pay-at-piece", "scored-length", "skip-room",
    "skip-two-token", "span-now", "step-at-shut", "step-before-lay", "sum-positions",
    "void-zero", "width-now",
]

for _build in emit.READINGS:
    _build()
READINGS = dict(emit.BUILT)
assert sorted(EDITS) == sorted(READINGS), "EDITS and emit.py have drifted apart"

_TREES = {}


def run(policy, text):
    """Replay one shard under one directory of the six modules."""
    here = _TREES.get(str(policy))
    if here is None:
        here = _TREES[str(policy)] = lab.tree(policy)
    room = pathlib.Path(tempfile.mkdtemp(prefix="pss-read-"))
    shard = room / "s.txt"
    shard.write_text(text.rstrip("\n") + "\n", encoding="utf-8", newline="\n")
    try:
        return lab.run(here, shard, timeout=60)
    except RuntimeError as exc:
        return ["RAISED", str(exc).splitlines()[-1]]
    except Exception as exc:
        return ["RAISED", type(exc).__name__]


def enumerated():
    return [(name, "\n".join(cases.ops(name))) for name in cases.ORDER]


def generated(n):
    out = []
    small = [f for f, big in gen.FAMILIES if not big]
    per = max(1, n // len(small))
    for fam in small:
        for i in range(per):
            name = "%s-%d" % (fam, i)
            out.append((name, "\n".join(gen.one(fam, "reading/%s" % name))))
    return out


def reductions(text):
    """Structure-aware shrinking: drop a record, or a settings op, keeping the head and seal."""
    lines = text.split("\n")
    head = [i for i, l in enumerate(lines) if i < 3]
    for i in range(len(lines) - 1, -1, -1):
        if i in head or lines[i] == "seal":
            continue
        yield "\n".join(lines[:i] + lines[i + 1:])
    for i, l in enumerate(lines):
        w = l.split()
        if w and w[0] == "rec" and int(w[2]) > 2:
            for n in (2, int(w[2]) // 2):
                if n >= 2 and n != int(w[2]):
                    yield "\n".join(lines[:i] + ["rec %s %d %s" % (w[1], n, w[3])] + lines[i + 1:])
