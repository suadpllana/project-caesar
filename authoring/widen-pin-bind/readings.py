"""Does the enumerated set separate the wrong readings a solver will actually have?

Per-rule coverage on paper is not coverage. A reading that no enumerated case fails is one a
submission carries all the way to the generated population, where the failure reads as bad
luck rather than as a named rule.

The readings come from emit.py, so the cheats that ship and the readings measured here are the
same files and cannot drift apart. Run emit.py first, always.

    python tools/readingcheck.py widen-pin-bind [rounds]
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

# The same names again, as a literal table, because tools/tracecheck.py reads this file
# without importing it and has to see every reading that must carry a row in trace.md.
EDITS = (
    "amb-tie", "arity-any", "bind-post", "bound-flip", "bound-skip", "lex-first",
    "memo-flat", "memo-site", "nest-bottom", "one-amb", "open-first", "open-high",
    "open-minimal", "path-any", "path-long", "pin-blind", "pin-eager", "pin-first",
    "pin-refresh", "ret-free", "ret-nocheck", "slots-left", "sum-lowest", "tally-slots",
)
assert set(EDITS) == set(READINGS), sorted(set(EDITS) ^ set(READINGS))


def run(policy, text):
    """Drive one program under one directory of the six files."""
    return lab.run_text(policy, text if text.endswith("\n") else text + "\n")


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
    """Drop one line at a time, and drop an expression together with the values it needs.

    A declaration line cannot be dropped on its own when something below it names the kind,
    so most single-line reductions produce a program that raises under both policies, which
    the shrinker reads as no difference and passes over. Dropping the expressions first is
    what gets a counterexample down to something short enough to read.
    """
    rows = text.split("\n")
    asks = [i for i, row in enumerate(rows) if row.strip().startswith("ask ")]
    for i in reversed(asks):
        yield "\n".join(rows[:i] + rows[i + 1:])
    for i in range(len(rows) - 1, -1, -1):
        if i in asks:
            continue
        yield "\n".join(rows[:i] + rows[i + 1:])
