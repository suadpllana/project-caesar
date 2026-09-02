"""The graded decisions the reference makes, as rows of primitive features.

tools/onelinecheck.py reads this and searches for the shortest exact rule over the
features. The point is the easiness probe asked mechanically: a graded decision a
two-term comparison reproduces is an answer a frontier model writes cold, whatever
the surrounding prose says.

The features are deliberately primitive - things a solver can read off the state
without having worked anything out: how far up the bucket's last stamp is, how many
nodes hold anything, how many sources are still open, how far the lowest source
floor is, whether anything sits in this gather's own inbox, how many buckets it has
open, whether the graph has a way back into this gather and whether a lift sits
anywhere on a route into it. Derived quantities are kept out on purpose. "The
earliest stamp that can still reach this gather" would make the whole thing a
one-term comparison, and computing it is the task.
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

ROUNDS = 120


def look(st, gn, b, g):
    hi = (b + 1) * g.par[gn] - 1
    holds = 0
    for n in g.names:
        if st.box[n] or st.buk[n]:
            holds += 1
    live = [n for n in g.names if g.kind[n] == "src" and not st.shut[n]]
    floor = min([st.low[n] for n in live], default=-1)
    back = 0
    seen, front = set(), [d for d, lag in g.out[gn]]
    while front:
        n = front.pop()
        if n in seen:
            continue
        seen.add(n)
        front.extend(d for d, lag in g.out[n])
    if gn in seen:
        back = 1
    lifts = sum(1 for n in g.names if g.kind[n] == "lift")
    return {
        "hi": hi,
        "holds": holds,
        "open_src": len(live),
        "floor": floor,
        "inbox": len(st.box[gn]),
        "buckets": len(st.buk[gn]),
        "loop": back,
        "lifts": lifts,
        "gap": floor - hi if floor >= 0 else 99,
    }


def samples():
    rows = {"seal-now": []}
    app = harness.tree(os.path.join(ROOT, "solution"))
    try:
        import importlib
        sys.path.insert(0, str(app))
        harness.unload()
        gr = importlib.import_module("flow.gr")
        mach = importlib.import_module("flow.mach")
        due = importlib.import_module("flow.due")
        real = due.ripe

        def spy(st, gn, b):
            out = real(st, gn, b)
            rows["seal-now"].append((look(st, gn, b, st.g), bool(out)))
            return out

        due.ripe = spy
        mach.due.ripe = spy
        texts = [cases.PLANS[n] for n in sorted(cases.PLANS)]
        texts += [gen.text(p) for _, p in gen.batch("decide", ROUNDS)]
        for text in texts:
            mach.Mach(gr.parse(text), lambda r: None).run()
        due.ripe = real
        sys.path.remove(str(app))
        harness.unload()
    finally:
        import shutil
        shutil.rmtree(app.parent, ignore_errors=True)
    return rows


if __name__ == "__main__":
    got = samples()
    for k in sorted(got):
        yes = sum(1 for _, y in got[k] if y)
        print("%s: %d samples, %d true" % (k, len(got[k]), yes))
