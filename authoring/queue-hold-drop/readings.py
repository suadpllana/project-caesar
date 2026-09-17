"""Does the enumerated set separate the wrong readings a solver will actually have?

Per-rule coverage on paper is not coverage. A reading that no shipped case fails is either a
hole - it would survive the hand set and die on a generated program, which reads as bad luck
rather than as a broken rule - or it is a correct variant and the rule behind it is a sentence
with nothing under it.

The readings come from `emit.py`, so the cheats that ship and the readings measured here are the
same files and cannot drift apart.

    python tools/readingcheck.py queue-hold-drop [rounds]
"""
import pathlib
import random
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import emit  # noqa: E402
import lab  # noqa: E402

sys.path.insert(0, str(lab.TASK / "tests"))
import cases  # noqa: E402
import gen  # noqa: E402

REFERENCE = str(lab.TASK / "solution")

# Every semantic reading emit.py knows how to build. The two right-but-slow services, the forgery
# and the isolation probes are not readings of the rules and are not measured here.
READINGS = dict(emit.BUILT)

# The same names again as plain text, so tools/tracecheck.py can require a row for each.
EDITS = [
    "ack-early",
    "add-set",
    "ans-front",
    "ask-base",
    "gone-all",
    "gone-both",
    "gone-flat",
    "gone-one",
    "hold-new-free",
    "hold-no-spread",
    "id-at-send",
    "lay-upsert",
    "mov-cycle",
    "name-mov-flat",
    "order-name",
    "reach-fixed",
    "reach-kids",
    "say-unsorted",
    "stop-only",
    "stop-queued",
    "take-twice",
    "view-skip-sent",
    "zero-hidden",
]

assert sorted(EDITS) == sorted(READINGS), "EDITS has drifted from what emit.py builds"

_TREES = {}


def run(policy, text):
    """Drive one program under one directory of the six files."""
    here = _TREES.get(str(policy))
    if here is None:
        here = _TREES[str(policy)] = lab.tree(policy)
    lines = [line for line in text.splitlines() if line.strip()]
    try:
        return lab.drive(here, lines)
    except Exception as exc:  # a reading that cannot run is still separated
        return ["RAISED", str(exc).splitlines()[-1]]


def enumerated():
    return [(name, "\n".join(cases.ops(name))) for name in cases.ORDER]


def generated(n):
    out = []
    small = [fam for fam, big in gen.FAMILIES if not big]
    for i in range(n):
        fam = small[i % len(small)]
        r = random.Random("reading|%s|%d" % (fam, i))
        out.append(("%s-%d" % (fam, i), "\n".join(gen.build(fam, r, small=True))))
    return out
