"""Does the enumerated set separate the wrong readings a solver will actually have?

The readings come from emit.py, so the cheats that ship and the readings measured here are the
same files and cannot drift apart. Run emit.py first, always.

    python tools/readingcheck.py row-anchor-pass [rounds]
"""
import pathlib
import random
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import emit  # noqa: E402
import lab  # noqa: E402

cases, gen, _model = lab.sealed()

REFERENCE = str(lab.SOL)

for _build in emit.READING_BUILDERS:
    _build()
READINGS = dict(emit.READINGS)

_TREES = {}


def run(policy, text):
    """Drive one program under one directory of the six files."""
    here = _TREES.get(str(policy))
    if here is None:
        here = _TREES[str(policy)] = lab.tree(policy)
    try:
        return lab.run_text(here, text)
    except Exception as exc:  # noqa: BLE001
        return ["raised %s" % type(exc).__name__]


def enumerated():
    return [(name, "\n".join(cases.prog(name))) for name in cases.ORDER]


def generated(n):
    out = []
    small = [f for f, big in gen.FAMILIES if not big]
    per = max(1, n // len(small))
    for fam in small:
        for i in range(per):
            rng = random.Random("reading|%s|%d" % (fam, i))
            out.append(("%s-%d" % (fam, i), "\n".join(gen.MAKERS[fam](rng))))
    return out


def reductions(text):
    """Drop one event at a time, then one group with its edits, then shorten a group."""
    lines = text.split("\n")
    head = [ln for ln in lines if ln.split()[:1] in (["cfg"], ["g"])]
    evs = [ln for ln in lines if ln.split()[:1] not in (["cfg"], ["g"])]
    for i in range(len(evs) - 1, -1, -1):
        if len(evs) > 1:
            yield "\n".join(head + evs[:i] + evs[i + 1:])
    for i, ln in enumerate(head):
        bits = ln.split()
        if bits[0] == "g" and int(bits[5]) > 0:
            bits2 = bits[:5] + [str(int(bits[5]) - 1)]
            yield "\n".join(head[:i] + [" ".join(bits2)] + head[i + 1:] + evs)
