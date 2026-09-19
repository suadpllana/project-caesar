"""Does the enumerated set separate the wrong readings a solver will actually have?

Per-rule coverage on paper is not coverage. A reading that no enumerated case fails is a
reading a submission can carry all the way to the generated population, where a failure reads
as bad luck rather than as a named rule - one of the causes behind a zero-solve rejection.

The readings come from emit.py, so the cheats that ship and the readings measured here are the
same files and cannot drift apart. Run emit.py first, always.

    python tools/readingcheck.py referential-action-order [rounds]
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
    """Structure-aware shrinking: drop one line at a time, schema lines last.

    A `tab` or `link` line cannot go on its own without leaving the lines that name it
    dangling, so the shrinker drops the row ops first and only then tries the schema, which
    keeps the shrunk program a program rather than a parse error.
    """
    lines = text.splitlines()
    rows = [i for i, ln in enumerate(lines) if ln.split()[:1] and
            lines[i].split()[0] in ("put", "out", "mov")]
    head = [i for i in range(len(lines)) if i not in rows]
    for i in rows + head:
        yield "\n".join(lines[:i] + lines[i + 1:])
