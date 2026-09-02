"""Plausible-but-wrong readings of the round rules, as the files they would replace.

`tools/readingcheck.py` runs each of these against the reference over the enumerated set
first and then over generated streams. A reading the enumerated set does not separate is a
reading a probe agent can carry all the way to the verifier and lose on six streams out of
three hundred, which under all-or-nothing grading is indistinguishable from bad luck.
"""
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
REFERENCE = ROOT / "solution"

_HOLD = '''def draw(b, cap):
    d = {n: 0 for n in b.who()}
    h = {n: b.hold(n) for n in b.who()}
    on = True
    while on:
        on = False
        for n in b.who():
            q = b.line(n)
            while d[n] < cap[n]:
                o = q[d[n]]
                if h[n] < o.am:
                    break
                h[n] -= o.am
                h[o.pe] += o.am
                d[n] += 1
                on = True
    return d
'''

_HEADS = '''def draw(b, cap):
    who = b.who()
    ln = {n: b.line(n) for n in who}
    d = {n: 0 for n in who}
    h = {n: b.hold(n) for n in who}
    while True:
        s = [n for n in who if d[n] < cap[n]]
        while True:
            o = {n: 0 for n in who}
            i = {n: 0 for n in who}
            for n in s:
                x = ln[n][d[n]]
                o[n] += x.am
                i[x.pe] += x.am
            bad = [n for n in s if h[n] + i[n] - o[n] < 0]
            if not bad:
                break
            s.remove(bad[0])
        if not s:
            return d
        for n in s:
            x = ln[n][d[n]]
            h[n] -= x.am
            h[x.pe] += x.am
            d[n] += 1
'''

_NOSHORT = '''def draw(b, cap):
    return dict(cap)
'''

_BULK = '''def give(b, cap, plan):
    out = []
    for n in b.who():
        q = b.line(n)
        for k in range(plan.get(n, 0), cap[n]):
            out.append(q[k])
    out.sort(key=lambda o: o.sq)
    return [o.i for o in out]
'''

_NEWEST = '''def give(b, cap, plan):
    out = []
    for n in b.who():
        q = b.line(n)
        for k in range(plan.get(n, 0), cap[n]):
            out.append(q[k])
    if not out:
        return []
    out.sort(key=lambda o: o.sq)
    return [out[-1].i]
'''

_ONEPASS = '''from house import drn
from house import due
from house import gvp


def turn(b, t):
    b.roll(t)
    z = {n: 0 for n in b.who()}
    cap = due.reach(b, t)
    plan = drn.draw(b, cap)
    b.move(plan)
    cap = due.reach(b, t)
    for i in gvp.give(b, cap, z):
        b.drop(i)
    b.shut()
'''

_SETDUE = '''def reach(b, t):
    c = {}
    for n in b.who():
        c[n] = sum(1 for o in b.line(n) if o.dt <= t)
    return c
'''

_ALLDUE = '''def reach(b, t):
    return {n: len(b.line(n)) for n in b.who()}
'''

READINGS = {
    "pay-what-you-hold": {"drn.py": _HOLD},
    "net-the-heads": {"drn.py": _HEADS},
    "never-short-of-anything": {"drn.py": _NOSHORT},
    "give-up-in-bulk": {"gvp.py": _BULK},
    "give-up-newest": {"gvp.py": _NEWEST},
    "one-pass-round": {"rnd.py": _ONEPASS},
    "blocker-does-not-block": {"due.py": _SETDUE},
    "day-does-not-matter": {"due.py": _ALLDUE},
}


import sys

sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "tests"))

import gen  # noqa: E402
import harness  # noqa: E402
import oracle  # noqa: E402
import scen  # noqa: E402


def run(policy, text):
    """The canonical form the verifier compares, so a reading is only called separated when
    the grader would actually fail it - not when it merely wrote the same round down in a
    different order."""
    r = harness.run(policy, text)
    return (oracle.rounds([list(x) for x in r["log"]]), r["sheet"])


def enumerated():
    return list(scen.STREAMS)


def generated(n):
    return gen.batch("5eed10ad5eed10ad", n)
