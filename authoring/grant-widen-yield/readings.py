"""Does the enumerated set separate the wrong readings a solver will actually have?

Per-rule coverage on paper is not coverage. A reading that no enumerated case fails is a
reading a submission can carry all the way to the generated population, where a failure reads
as bad luck rather than as a named rule - one of the causes behind a zero-solve rejection.

The readings come from emit.py, so the cheats that ship and the readings measured here are the
same files and cannot drift apart. Run emit.py first, always.

    python tools/readingcheck.py grant-widen-yield [rounds]
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


# The same names again as a literal, so tools that read this file without importing
# it (tracecheck) see the reading list. Kept honest by the assertion below.
EDITS = (
    "give-claim-all",
    "give-claim-eff",
    "give-node-only",
    "hold-ask-wins",
    "hold-forgets-ask",
    "hold-never-falls",
    "hold-shallow-walk",
    "keep-fixpoint",
    "keep-order-deep",
    "keep-order-made",
    "keep-try-all",
    "mode-cov-six",
    "mode-cov-write",
    "mode-sup-top",
    "step-drop-keeps",
    "step-give-any",
    "step-grants-walked",
    "step-inner-first",
    "step-lookahead",
    "step-no-sweep",
    "step-refuse-any",
    "step-shut-silent",
    "step-wide-first",
    "step-young-first",
    "wide-at-limit",
    "wide-blocks-first",
    "wide-counts-claims",
    "wide-once",
    "wide-preempts",
)

assert sorted(READINGS) == sorted(EDITS), "EDITS has drifted from emit.READINGS"

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
            out.append(("%s-%d" % (fam, i), "\n".join(gen.MAKE[fam](rng))))
    return out


def reductions(text):
    """Structure-aware shrinking: drop a statement, or a whole transaction.

    A program is lines, but a transaction is a region: dropping its `open` on its own leaves
    every later line referring to a transaction with no age, which raises rather than shrinks.
    """
    lines = text.split("\n")
    for i, line in enumerate(lines):
        if line.split()[:1] in (["take"], ["drop"], ["shut"]):
            yield "\n".join(lines[:i] + lines[i + 1:])
    names = [line.split()[1] for line in lines if line.startswith("open ")]
    for who in names:
        kept = [line for line in lines
                if not (line.startswith("open " + who) or " %s " % who in " " + line + " "
                        or line.split()[1:2] == [who])]
        if len(kept) < len(lines):
            yield "\n".join(kept)
