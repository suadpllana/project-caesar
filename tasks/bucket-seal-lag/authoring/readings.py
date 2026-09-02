"""The plausible-but-wrong readings, for tools/readingcheck.py.

Per-rule coverage on paper is not coverage. The question a hand-written case set
cannot answer by inspection is whether a *specific* wrong reading survives it, and
the only way to know is to write that reading down and run it. These are the same
readings the cheat suite ships, taken from the one place they are defined so the
two cannot drift.
"""

import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "tests"))

import cases
import emit as gen
import harness
import gen as plans

REFERENCE = os.path.join(ROOT, "solution")


def build():
    ref = gen.refset()
    out = {}
    for name, fn, old, new, note in gen.SWAPS:
        if ref[fn].count(old) != 1:
            raise SystemExit("anchor missed for %s" % name)
        out[name] = {fn: ref[fn].replace(old, new)}
    return out


READINGS = build()


def run(policy, text):
    got = harness.run(policy, text)
    return (tuple(tuple(map(str, r)) for r in got["tr"]),
            tuple(sorted((k, tuple(v)) for k, v in got["sk"].items())))


def enumerated():
    return [(n, cases.PLANS[n]) for n in sorted(cases.PLANS)]


def generated(n):
    return [(nm, plans.text(p)) for nm, p in plans.batch("readings", n)]
