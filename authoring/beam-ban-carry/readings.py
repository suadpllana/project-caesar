"""Does the enumerated set separate the wrong readings a solver will actually have?

Per-rule coverage on paper is not coverage. A reading that no enumerated case fails is a
reading a submission can carry all the way to the generated population, where a failure reads
as bad luck rather than as a named rule.

The readings come from emit.py, so the cheats that ship and the readings measured here are the
same files and cannot drift apart. Run emit.py first, always.

    python tools/readingcheck.py beam-ban-carry [rounds]
"""
import pathlib
import random
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import emit  # noqa: E402
import gen  # noqa: E402
import lab  # noqa: E402

sys.path.insert(0, str(lab.TASK / "tests"))
import cases  # noqa: E402

REFERENCE = str(lab.TASK / "solution")
READINGS = dict(emit.READINGS)

_TREES = {}


def run(policy, text):
    """Drive one program under one directory of the six files."""
    key = str(policy)
    if key not in _TREES:
        _TREES[key] = lab.loader(lab.tree(policy))
    return _TREES[key](text if text.endswith("\n") else text + "\n")


def enumerated():
    return [(name, "\n".join(cases.prog(name))) for name in cases.ORDER]


def generated(n):
    out = []
    small = [f for f, big in gen.FAMILIES if not big]
    per = max(1, n // len(small))
    for fam in small:
        for i in range(per):
            rng = random.Random("reading|%s|%d" % (fam, i))
            out.append(("%s-%d" % (fam, i), "\n".join(gen.make(fam, rng))))
    return out


def reductions(text):
    """Structure-aware shrinking: drop a request, drop a scoring row, shorten a prompt."""
    lines = text.split("\n")
    for i, line in enumerate(lines):
        if line.startswith("sc ") or line.startswith("ask "):
            trial = lines[:i] + lines[i + 1:]
            if any(l.startswith("ask") for l in trial):
                yield "\n".join(trial)
    for i, line in enumerate(lines):
        if line.startswith("ask ") and len(line.split()) > 3:
            yield "\n".join(lines[:i] + [" ".join(line.split()[:-1])] + lines[i + 1:])
