"""Does the enumerated set separate the wrong readings a solver will actually have?

The readings come from emit.py, so the cheats that ship and the readings measured here are the
same files and cannot drift apart. Run emit.py first, always.

    python tools/readingcheck.py owed-check-rewind [rounds]
"""
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
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
    return lab.run_text(here, text if text.endswith("\n") else text + "\n")


def enumerated():
    return [(name, "\n".join(cases.prog(name))) for name in cases.ORDER]


def generated(n):
    out = []
    small = [f for f, big in gen.FAMILIES if not big]
    per = max(1, n // len(small))
    for fam in small:
        for i in range(per):
            rng = random.Random("reading|%s|%d" % (fam, i))
            out.append(("%s-%d" % (fam, i), "\n".join(gen.build(fam, rng))))
    return out


def reductions(text):
    """Structure-aware shrinking: drop a statement, a whole transaction, a row, or a constraint.

    Dropping one line of a transaction can leave `commit` without its `begin`, which is a
    different program rather than a smaller one, so transactions go as a unit too.
    """
    lines = text.split("\n")
    heads = [i for i, ln in enumerate(lines) if ln.split()[:1] == ["begin"]]
    for n, i in enumerate(heads):
        j = heads[n + 1] if n + 1 < len(heads) else len(lines)
        yield "\n".join(lines[:i] + lines[j:])
    for i, ln in enumerate(lines):
        w = ln.split()[:1]
        if w in (["row"], ["check"]) or (w and w[0] not in ("table", "fk", "begin", "commit",
                                                          "rollback")):
            yield "\n".join(lines[:i] + lines[i + 1:])
