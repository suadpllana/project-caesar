"""The graded decisions the reference makes, as rows of primitive features.

tools/onelinecheck.py reads this and searches for the shortest exact rule over the
features. The point of the exercise is the easiness probe asked mechanically: a graded
decision that a two-term comparison reproduces is an answer a frontier model writes cold,
whatever the surrounding prose says.

The features are deliberately primitive - things a solver can read off the chain without
having worked anything out: how long the chain is, how many guards in it are marked, how
many carry a shield, where the innermost shield sits, where the outermost and innermost
marked guards sit, and for the resting question whether this guard is the one the cut was
raised for. Derived quantities are kept out on purpose. "How many marked guards are inside
the visibility window" would make the resting rule a two-term comparison, but computing it
already requires the window rule, which is the first thing a solver has to find.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "tests"))

import cases
import gen
import harness

ROUNDS = 250


def scan(ch):
    n = len(ch)
    marked = [i for i, g in enumerate(ch) if g.hit]
    shields = [i for i, g in enumerate(ch) if g.sh]
    return {
        "depth": n,
        "marked": len(marked),
        "shields": len(shields),
        "inshield": shields[-1] if shields else -1,
        "outmark": marked[0] if marked else -1,
        "inmark": marked[-1] if marked else -1,
    }


def collect():
    dst = harness.tree(os.path.join(ROOT, "solution"))
    harness.mount(dst)
    harness.drop()
    from kern import knot, pick, stop
    from kern.lex import parse
    from kern.loop import Loop

    out = {"delivery": [], "rest": [], "band-close": []}
    real_pick, real_stops, real_shut = pick.pick, stop.stops, knot.shut

    def spy_pick(f, ch):
        got = real_pick(f, ch)
        row = scan(ch)
        row["kid"] = 1 if f.inh else 0
        idx = -1
        for i, g in enumerate(ch):
            if g is got:
                idx = i
        out["delivery"].append((row, idx))
        return got

    def spy_stops(g, ch, gg):
        got = real_stops(g, ch, gg)
        row = scan(ch)
        row["ghit"] = 1 if g.hit else 0
        row["gsh"] = 1 if g.sh else 0
        row["stamp"] = 1 if g is gg else 0
        out["rest"].append((row, bool(got)))
        return got

    def spy_shut(bd, ch, g):
        got = real_shut(bd, ch, g)
        row = scan(ch)
        row["errs"] = len(bd.errs)
        row["own"] = 1 if g is bd.gd else 0
        row["none"] = 1 if g is None else 0
        out["band-close"].append((row, {None: 0}.get(got, 1 if got and got[0] == "cut" else 2)))
        return got

    pick.pick, stop.stops, knot.shut = spy_pick, spy_stops, spy_shut
    pool = [cases.PROGS[n] for n in sorted(cases.PROGS)]
    pool += [gen.text(p) for _, p in gen.batch("decide", ROUNDS)]
    for text in pool:
        rows = []
        try:
            Loop(parse(text), rows.append).run("main")
        except Exception:
            continue
    pick.pick, stop.stops, knot.shut = real_pick, real_stops, real_shut
    return out


_CACHE = {}


def samples():
    if not _CACHE:
        _CACHE.update(collect())
    return _CACHE


if __name__ == "__main__":
    got = samples()
    for k in sorted(got):
        print("%-14s %d samples" % (k, len(got[k])))
