"""Does the enumerated set separate the wrong readings a solver will actually have?

Per-rule coverage on paper is not coverage. A reading that no enumerated case fails is a
reading a submission can carry all the way to the generated population, where a failure reads
as bad luck rather than as a named rule - one of the causes behind a zero-solve rejection.

The readings come from emit.py, so the cheats that ship and the readings measured here are the
same files and cannot drift apart. Run emit.py first, always.

    python tools/readingcheck.py feed-lag-pare [rounds]
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
            out.append(("%s-%d" % (fam, i), "\n".join(gen.MAKERS[fam](rng))))
    return out


def reductions(text):
    """Shrinking that keeps a program well formed.

    Dropping a line at random is not enough: a `read` or an `ack` naming a pin whose `mark`
    or `feed` line has gone raises rather than shrinking, and a program that raises separates
    every reading for the wrong reason. So a pin is only dropped together with everything
    that names it, and an entry line is only dropped when nothing downstream depends on its
    sequence number - which nothing does, because every position in the brief is named by a
    pin rather than by a literal, except in an `ack`, whose argument is clamped instead.
    """
    lines = text.strip().splitlines()
    out = []
    for i, line in enumerate(lines):
        bits = line.split()
        if not bits:
            continue
        if bits[0] in ("set", "add", "del"):
            out.append("\n".join(lines[:i] + _reack(lines[i + 1:])))
        elif bits[0] in ("mark", "feed"):
            name = bits[1]
            out.append("\n".join(
                row for j, row in enumerate(lines)
                if j != i and not _names(row, name)))
        elif bits[0] in ("read", "pare", "ack", "unmark", "close"):
            out.append("\n".join(lines[:i] + lines[i + 1:]))
    return [o for o in out if o.strip()]


def _names(row, name):
    bits = row.split()
    return len(bits) > 1 and bits[1] == name


def _reack(rest):
    """After an entry is dropped every sequence number below it moves down by one."""
    out = []
    for row in rest:
        bits = row.split()
        if bits and bits[0] == "ack":
            out.append("ack %s %d" % (bits[1], max(0, int(bits[2]) - 1)))
        else:
            out.append(row)
    return out
