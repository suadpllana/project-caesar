"""Does the enumerated set separate the wrong readings a solver will actually have?

Per-rule coverage on paper is not coverage. A reading no enumerated case fails is one a
submission can carry all the way into the generated population, where the failure reads as bad
luck rather than as a named rule.

The readings come from emit.py, so the cheats that ship and the readings measured here are the
same sources and cannot drift. Run emit.py first, always.

    python tools/readingcheck.py stale-cover-serve [rounds]
"""
import pathlib
import random
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import emit  # noqa: E402
import lab  # noqa: E402

REFERENCE = str(lab.SOL)
READINGS = dict(emit.READINGS)
READINGS.update(emit.SHORTCUTS)

cases = lab.cases()
gen = lab.gen()

_TREES = {}


def run(policy, text):
    here = _TREES.get(str(policy))
    if here is None:
        here = _TREES[str(policy)] = lab.tree(policy)
    return lab.run_text(here, text if text.endswith("\n") else text + "\n")


def enumerated():
    return [(name, "\n".join(cases.prog(name))) for name in cases.ORDER]


def generated(n):
    out = []
    per = max(1, n // len(gen.SMALL))
    for fam in gen.SMALL:
        for i in range(per):
            rng = random.Random("reading|%s|%d" % (fam, i))
            out.append(("%s-%d" % (fam, i), "\n".join(gen.BUILD[fam](rng))))
    return out


def reductions(text):
    """Structure-aware shrinking.

    A program is lines, but a commit is a boundary: dropping a `w` line on its own moves its
    key out of the batch rather than making the program smaller, and dropping a `c` merges two
    batches into one. Offering whole write-commit groups and whole reads keeps every candidate
    a program of the same shape, which is what gets the counterexample short enough to ship.
    """
    lines = text.split("\n")
    head = lines[0] if lines and lines[0].startswith("h ") else None
    body = lines[1:] if head else lines

    groups = []
    run = []
    for line in body:
        run.append(line)
        if line.startswith("c") or line.startswith("r "):
            groups.append(run)
            run = []
    if run:
        groups.append(run)

    for i in range(len(groups) - 1, -1, -1):
        kept = groups[:i] + groups[i + 1:]
        flat = [x for g in kept for x in g]
        yield "\n".join(([head] if head else []) + flat)

    for i in range(len(body) - 1, -1, -1):
        if body[i].startswith("c"):
            continue
        yield "\n".join(([head] if head else []) + body[:i] + body[i + 1:])
