"""Does the enumerated set separate the wrong readings a solver will actually have?

Per-rule coverage on paper is not coverage: a reading no enumerated case fails is one a
submission can carry all the way into the generated population, where the failure reads as
bad luck rather than as a named rule.

The readings come from emit.py, so the files measured here and the files the cheats install
are the same and cannot drift apart. Run emit.py first, always.

    python tools/readingcheck.py page-bound-cut [rounds]
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
READINGS = dict(emit.READINGS)

_TREES = {}


def run(policy, text):
    """Drive one program under one directory of the five files."""
    here = _TREES.get(str(policy))
    if here is None:
        here = _TREES[str(policy)] = lab.tree(policy)
    return lab.run_text(here, text if text.endswith("\n") else text + "\n")


def enumerated():
    return [(name, "\n".join(cases.prog(name)) + "\n") for name in cases.ORDER]


def generated(n):
    out = []
    per = max(1, n // len(gen.FAMILIES))
    for row in gen.FAMILIES:
        for i in range(per):
            out.append(("%s-%d" % (row[0], i), gen.build(row, 90000 + i)))
    return out


def reductions(text):
    """Shorter programs to try when shrinking a counterexample: drop one operation."""
    lines = text.splitlines()
    head, ops = lines[0], lines[1:]
    for i in range(len(ops) - 1, -1, -1):
        if len(ops) > 1:
            yield "\n".join([head] + ops[:i] + ops[i + 1:]) + "\n"
