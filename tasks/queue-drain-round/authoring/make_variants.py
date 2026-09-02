"""Generate authoring/variants/ from the reference plus one declared override each.

A variant is the reference with one decision expressed differently, so every other file in
it is the reference's file by construction. Hand-copying them is how a variant suite starts
disagreeing with the reference the moment the reference changes, and the symptom is every
correct implementation failing at once, which reads like a broken reference.
"""
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
REF = HERE.parent / "solution"
OUT = HERE / "variants"

SET_SHRINK = '''def draw(b, cap):
    who = b.who()
    ln = {n: b.line(n) for n in who}
    take = {n: list(range(cap[n])) for n in who}
    while True:
        got = {n: 0 for n in who}
        for n in who:
            for k in take[n]:
                o = ln[n][k]
                got[o.pe] += o.am
        short = []
        for n in who:
            pay = sum(ln[n][k].am for k in take[n])
            if b.hold(n) + got[n] - pay < 0:
                short.append(n)
        if not short:
            return {n: len(take[n]) for n in who}
        take[short[0]].pop()
'''

RECOMPUTE = '''def _fits(b, ln, d, n):
    inc = 0
    for m in b.who():
        for o in ln[m][: d[m]]:
            if o.pe == n:
                inc += o.am
    pay = sum(o.am for o in ln[n][: d[n]])
    return b.hold(n) + inc - pay >= 0


def draw(b, cap):
    who = b.who()
    ln = {n: b.line(n) for n in who}
    d = dict(cap)
    moved = True
    while moved:
        moved = False
        for n in who:
            while d[n] > 0 and not _fits(b, ln, d, n):
                d[n] -= 1
                moved = True
    return d
'''

GIVE_FIRST = '''from house import drn
from house import due
from house import gvp


def turn(b, t):
    b.roll(t)
    z = {n: 0 for n in b.who()}
    while True:
        cap = due.reach(b, t)
        plan = drn.draw(b, cap)
        hand = gvp.give(b, cap, plan)
        if sum(plan.values()) == 0:
            if not hand:
                break
            for i in hand:
                b.drop(i)
            continue
        b.move(plan)
    b.shut()
'''

COLLECT = '''from house import drn
from house import due
from house import gvp


def turn(b, t):
    b.roll(t)
    z = {n: 0 for n in b.who()}
    go = True
    while go:
        cap = due.reach(b, t)
        plan = drn.draw(b, cap)
        b.move(plan)
        cap = due.reach(b, t)
        hand = list(gvp.give(b, cap, z))
        go = bool(hand)
        while hand:
            b.drop(hand.pop(0))
    b.shut()
'''

TAKEWHILE = '''import itertools


def reach(b, t):
    return {n: len(list(itertools.takewhile(lambda o: o.dt <= t, b.line(n)))) for n in b.who()}
'''

MIRROR = '''def draw(b, cap):
    who = list(reversed(b.who()))
    ln = {n: b.line(n) for n in who}
    d = {n: cap[n] for n in who}
    while True:
        inc = {n: 0 for n in who}
        for n in who:
            for o in ln[n][: d[n]]:
                inc[o.pe] += o.am
        nd = {}
        for n in who:
            av = b.hold(n) + inc[n]
            s = 0
            k = 0
            for o in ln[n][: d[n]]:
                if s + o.am > av:
                    break
                s += o.am
                k += 1
            nd[n] = k
        if nd == d:
            return d
        d = nd
'''

SPLIT = '''from house import drn
from house import due
from house import gvp


def turn(b, t):
    b.roll(t)
    z = {n: 0 for n in b.who()}
    while True:
        cap = due.reach(b, t)
        plan = drn.draw(b, cap)
        for n in reversed(b.who()):
            if plan.get(n, 0) > 0:
                b.move({n: plan[n]})
        cap = due.reach(b, t)
        hand = gvp.give(b, cap, z)
        if not hand:
            break
        for i in hand:
            b.drop(i)
    b.shut()
'''

VARIANTS = {
    "ok-move-in-parts": {"rnd.py": SPLIT},
    "ok-mirror-scan": {"drn.py": MIRROR},
    "ok-set-shrink": {"drn.py": SET_SHRINK},
    "ok-recompute": {"drn.py": RECOMPUTE},
    "ok-give-before-move": {"rnd.py": GIVE_FIRST},
    "ok-collect-then-drop": {"rnd.py": COLLECT},
    "ok-takewhile-cap": {"due.py": TAKEWHILE},
}


def main():
    for name, over in sorted(VARIANTS.items()):
        d = OUT / name
        if d.exists():
            shutil.rmtree(d)
        d.mkdir(parents=True)
        for f in sorted(REF.glob("*.py")):
            shutil.copy2(f, d / f.name)
        for fn, src in sorted(over.items()):
            (d / fn).write_text(src, newline="\n")
        (d / "README").write_text(
            "The reference with one decision written differently: %s\n" % ", ".join(sorted(over)),
            newline="\n",
        )
        print("wrote", d.name)


if __name__ == "__main__":
    main()
