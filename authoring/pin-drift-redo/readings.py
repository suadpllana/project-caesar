"""Does the enumerated set separate the wrong readings a solver will actually have?

Per-rule coverage on paper is not coverage. A reading that no enumerated case fails is a
reading a submission can carry all the way to the generated population, where a failure reads
as bad luck rather than as a named rule - one of the causes behind a zero-solve rejection.

The readings come from emit.py, so the cheats that ship and the readings measured here are the
same files and cannot drift apart. Run emit.py first, always.

    python tools/readingcheck.py pin-drift-redo [rounds]
"""
import pathlib
import random
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import emit  # noqa: E402
import lab  # noqa: E402

cases, gen, _model = lab.sealed()

REFERENCE = str(lab.TASK / "solution")

for _build in emit.READING_BUILDERS:
    _build()
READINGS = dict(emit.READINGS)

_TREES = {}


def run(policy, text):
    """Drive one program under one directory of the six files."""
    key = str(policy)
    here = _TREES.get(key)
    if here is None:
        here = _TREES[key] = lab.tree(pathlib.Path(policy))
    return lab.run_text(here, text)


def enumerated():
    return [(name, "\n".join(cases.prog(name))) for name in cases.ORDER]


def generated(n):
    out = []
    small = [f for f, big in gen.FAMILIES if not big]
    per = max(1, n // len(small))
    for fam in small:
        for i in range(per):
            rng = random.Random("reading|%s|%d" % (fam, i))
            out.append(("%s-%d" % (fam, i), "\n".join(gen.BUILD[fam](rng))))
    return out


def reductions(text):
    """Shrink a counterexample: drop one op line, or one whole transaction."""
    lines = text.split("\n")
    for i in range(1, len(lines)):
        yield "\n".join(lines[:i] + lines[i + 1:])
    nums = sorted({line.split()[1] for line in lines[1:] if len(line.split()) > 1})
    for num in nums:
        kept = [line for line in lines
                if len(line.split()) < 2 or line.split()[1] != num]
        if len(kept) < len(lines):
            yield "\n".join(kept)
