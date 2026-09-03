"""Write authoring/variants/ from the reference plus one declared override each.

A variant is the reference with one decision made differently, so every other
file in it is the reference's by construction. Hand-copied variants drift the
moment the reference changes, and the symptom is every correct implementation
disagreeing at once, which reads as a broken reference. Generating them makes
that impossible.
"""

import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.dirname(HERE)
REF = os.path.join(TASK, "solution")
OUT = os.path.join(HERE, "variants")
NAMES = ("rch.py", "hold.py", "card.py", "seq.py")


def ref(name):
    with open(os.path.join(REF, name)) as fh:
        return fh.read()


SPAN_BFS = '''# The same search, walking its frontier oldest first and keeping the groups it
# has already opened in a list rather than a set. Same answer, different order.
def span(bk, c):
    cells = bk.cells()
    ids = sorted(cells)
    seat = dict((i, set(cells[i])) for i in ids)
    near = dict((i, set()) for i in ids)
    for n in bk.open_tags():
        pool = set(bk.tags[n])
        hit = [i for i in ids if pool & seat[i]]
        for i in hit:
            near[i].update(j for j in hit if j != i)
    stop = set()
    for a, b in bk.bars:
        ra, rb = bk.find(a), bk.find(b)
        if ra != rb:
            stop.add((min(ra, rb), max(ra, rb)))
    line = [frozenset((c,))]
    done = []
    at = 0
    out = set()
    while at < len(line):
        grp = line[at]
        at += 1
        if grp in done:
            continue
        done.append(grp)
        out |= grp
        for i in sorted(grp):
            for j in sorted(near[i]):
                if j in grp:
                    continue
                if any((min(k, j), max(k, j)) in stop for k in grp):
                    continue
                wider = grp | {j}
                if wider not in line:
                    line.append(wider)
    out.discard(c)
    return out
'''

SPAN_KEYS = '''# The same search carried over sets of keys instead of sets of cells. A group is
# grown by absorbing whole cells, a bar forbids a group holding both of its keys,
# and the cells the groups cover are read off at the end.
def span(bk, c):
    cells = bk.cells()
    seat = dict((i, frozenset(cells[i])) for i in sorted(cells))
    tags = [sorted(bk.tags[n]) for n in bk.open_tags()]
    bars = sorted(bk.bars)
    start = seat[c]
    seen = set()
    work = [start]
    wide = set(start)
    while work:
        grp = work.pop()
        if grp in seen:
            continue
        seen.add(grp)
        wide |= grp
        for pool in tags:
            if not (set(pool) & grp):
                continue
            for k in pool:
                if k in grp:
                    continue
                bigger = grp | seat[bk.find(k)]
                if any(a in bigger and b in bigger for a, b in bars):
                    continue
                work.append(bigger)
    return set(i for i in sorted(cells) if i != c and (seat[i] & wide))
'''

HOLD_INLINE = '''# The same rule with the reach search folded in rather than asked for. Nothing
# calls rch.span; the declared file is left standing and the reasoning lives here.
from bind import card


def _open_groups(bk, c):
    cells = bk.cells()
    ids = sorted(cells)
    near = dict((i, set()) for i in ids)
    for n in bk.open_tags():
        pool = set(bk.tags[n])
        hit = [i for i in ids if pool & set(cells[i])]
        for i in hit:
            near[i].update(j for j in hit if j != i)
    stop = set()
    for a, b in bk.bars:
        ra, rb = bk.find(a), bk.find(b)
        if ra != rb:
            stop.add((min(ra, rb), max(ra, rb)))
    out = set()
    seen = set()
    work = [frozenset((c,))]
    while work:
        grp = work.pop()
        if grp in seen:
            continue
        seen.add(grp)
        out |= grp
        for i in sorted(grp):
            for j in sorted(near[i] - grp):
                if all((min(k, j), max(k, j)) not in stop for k in grp):
                    work.append(grp | {j})
    out.discard(c)
    return out


def firm(bk, c):
    a = card.auth(bk, c)
    if a is None:
        return False
    rep = bk.held(c)[0]
    reach = set(bk.held(c))
    for x in _open_groups(bk, c):
        keys = bk.held(x)
        if keys[0] < rep:
            return False
        b = card.auth(bk, x)
        if b is not None and b < a:
            return False
        reach.update(keys)
    for n in bk.open_runs():
        for k in bk.unsent(n):
            if k in reach and (n, k) < a:
                return False
    return True
'''

RCH_STUB = '''def span(bk, c):
    return set()
'''

CARD_SCAN = '''# The same row read off one pass with explicit comparisons instead of tuple
# ordering, and the smallest key taken by a running minimum rather than a sort.
def auth(bk, c):
    run, key = None, None
    for (n, k) in bk.post:
        if bk.find(k) != c:
            continue
        if run is None or n < run or (n == run and k < key):
            run, key = n, k
    return None if run is None else (run, key)


def card(bk, c):
    low = None
    for k in bk.held(c):
        if low is None or k < low:
            low = k
    a = auth(bk, c)
    return low, (bk.post[a] if a is not None else -1)
'''

SEQ_KEY = '''def queue(bk, ripe):
    return sorted(ripe, key=lambda k: (k,))
'''

PLAN = {
    "ok-frontier-order": {"rch.py": SPAN_BFS},
    "ok-group-of-keys": {"rch.py": SPAN_KEYS},
    "ok-reach-inline": {"hold.py": HOLD_INLINE, "rch.py": RCH_STUB},
    "ok-explicit-keys": {"card.py": CARD_SCAN, "seq.py": SEQ_KEY},
}

NOTE = {
    "ok-frontier-order": "The group search walks its frontier the other way round.",
    "ok-group-of-keys": "The group search carried over keys instead of cells.",
    "ok-reach-inline": "The reach search folded into the readiness test, so the\n"
                       "declared rch.py is never called. It is here to prove the\n"
                       "interpreter's tallies are floors and not equalities.",
    "ok-explicit-keys": "The row read off one pass with explicit comparisons, and\n"
                        "the filing order taken through an explicit sort key.",
}


def main():
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    for name, over in sorted(PLAN.items()):
        home = os.path.join(OUT, name)
        os.makedirs(home)
        for base in NAMES:
            body = over.get(base, ref(base))
            with open(os.path.join(home, base), "w", newline="\n") as fh:
                fh.write(body)
        with open(os.path.join(home, "README"), "w", newline="\n") as fh:
            fh.write(NOTE[name] + "\n")
        print("wrote", name, "overriding", sorted(over))
    return 0


if __name__ == "__main__":
    sys.exit(main())
