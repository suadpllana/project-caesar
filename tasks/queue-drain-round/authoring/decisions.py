"""The graded decisions the reference makes, as rows of integers an agent can read.

`tools/onelinecheck.py` searches these for the shortest exact rule over the fields the
environment already exposes. A graded decision a two-term rule reproduces is one a frontier
model writes cold, whatever the prose around it says, and it is an easiness rejection
waiting to happen.

Three questions are asked of every round the reference settles:

  head-moves      does the obligation at the front of this member's line move in this
                  round? The features are everything the book will tell you about that
                  member at that moment.
  depth           how far down this member's line does the round get?
  gives-up        is this reachable obligation the one the round hands back?
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "tests"))
sys.path.insert(0, str(ROOT / "environment" / "app_src"))

import gen  # noqa: E402
import scen  # noqa: E402


def _feat(b, n, cap, t):
    ln = b.line(n)
    reach = ln[: cap[n]]
    owed = sum(o.am for o in reach)
    owed_in = 0
    for m in b.who():
        for o in b.line(m)[: cap[m]]:
            if o.pe == n:
                owed_in += o.am
    head = reach[0].am if reach else 0
    return {
        "hold": b.hold(n),
        "head": head,
        "reach": len(reach),
        "line": len(ln),
        "owed": owed,
        "owed_in": owed_in,
        "spare": b.hold(n) + owed_in - owed,
        "afford": b.hold(n) - head,
        "tick": t,
    }


def samples():
    from house import bk, ev

    sys.path.insert(0, str(ROOT / "solution"))
    import importlib

    for m in ("house.drn", "house.gvp", "house.due"):
        if m in sys.modules:
            del sys.modules[m]
    drn = importlib.import_module("house.drn")
    due = importlib.import_module("house.due")
    ref_drn = importlib.util.spec_from_file_location("ref_drn", ROOT / "solution" / "drn.py")
    mod = importlib.util.module_from_spec(ref_drn)
    ref_drn.loader.exec_module(mod)
    ref_gvp = importlib.util.spec_from_file_location("ref_gvp", ROOT / "solution" / "gvp.py")
    gmod = importlib.util.module_from_spec(ref_gvp)
    ref_gvp.loader.exec_module(gmod)

    out = {"head-moves": [], "depth": [], "gives-up": []}
    streams = list(scen.STREAMS) + gen.batch("d3c1510n5", 10)
    for _name, text in streams:
        who, run, rows = ev.read(text)
        b = bk.Book(who, lambda *a: None)
        for t in range(1, run + 1):
            ev.feed(b, rows, t)
            b.roll(t)
            while True:
                cap = due.reach(b, t)
                plan = mod.draw(b, cap)
                for n in who:
                    if cap[n] == 0:
                        continue
                    f = _feat(b, n, cap, t)
                    out["head-moves"].append((f, bool(plan[n] > 0)))
                    out["depth"].append((f, plan[n]))
                b.move(plan)
                cap = due.reach(b, t)
                hand = gmod.give(b, cap, {n: 0 for n in who})
                left = [(n, k) for n in who for k in range(cap[n])]
                if not left:
                    break
                for n, k in left:
                    f = _feat(b, n, cap, t)
                    f = dict(f, place=k, age=b.line(n)[k].sq)
                    out["gives-up"].append((f, bool(hand and b.line(n)[k].i == hand[0])))
                for i in hand:
                    b.drop(i)
                if not hand:
                    break
            b.shut()
    return out
