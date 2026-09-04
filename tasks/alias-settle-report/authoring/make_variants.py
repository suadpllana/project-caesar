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
def span(bk, c, off):
    cells = bk.cells()
    ids = sorted(i for i in cells if not (set(cells[i]) & off))
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
# and the cells the groups cover are read off at the end. A cell that has gone is
# never absorbed and never reported.
def span(bk, c, off):
    cells = bk.cells()
    seat = dict((i, frozenset(cells[i])) for i in sorted(cells))
    here = sorted(i for i in cells if not (seat[i] & off))
    tags = [sorted(bk.tags[n]) for n in bk.open_tags()]
    bars = sorted(bk.bars)
    seen = set()
    work = [seat[c]]
    wide = set(seat[c])
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
                nxt = seat[bk.find(k)]
                if nxt & off:
                    continue
                bigger = grp | nxt
                if any(a in bigger and b in bigger for a, b in bars):
                    continue
                work.append(bigger)
    return set(i for i in here if i != c and (seat[i] & wide))
'''

HOLD_INLINE = '''# The same rule with the reach search folded in rather than asked for. Nothing
# calls rch.span; the declared file is left standing and the reasoning lives here.
from bind import card


def _open_groups(bk, c, off):
    cells = bk.cells()
    ids = sorted(i for i in cells if not (set(cells[i]) & off))
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


def sound(bk, c, off):
    a = card.auth(bk, c)
    if a is None:
        return False
    rep = bk.held(c)[0]
    reach = set(bk.held(c))
    for x in _open_groups(bk, c, off):
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


def firm(bk, c):
    off = set(bk.gone)
    ripe = set()
    moved = True
    while moved:
        moved = False
        for w in bk.watch:
            if w in bk.filed or w in ripe:
                continue
            d = bk.find(w)
            if set(bk.held(d)) & off:
                continue
            if sound(bk, d, off):
                ripe.add(w)
                off = off | set(bk.held(d))
                moved = True
    return any(bk.find(w) == c for w in ripe)
'''

RCH_STUB = '''def span(bk, c, off):
    return set()
'''

HOLD_ROUNDS = '''# The same smallest self-consistent set, grown by a worklist over cells rather
# than by rescanning the watch list, and starting from the far end of it. The
# order a cell is taken in cannot matter: letting a cell go only ever takes
# something out of another cell's reach, so nothing that was ready stops being
# ready, and the set the rounds close on is the same set.
from bind import card, rch


def sound(bk, c, off):
    a = card.auth(bk, c)
    if a is None:
        return False
    here = bk.held(c)
    rep = here[0]
    wide = set(here)
    for x in rch.span(bk, c, off):
        ks = bk.held(x)
        if ks[0] < rep:
            return False
        b = card.auth(bk, x)
        if b is not None and b < a:
            return False
        wide.update(ks)
    for n in bk.open_runs():
        for k in bk.unsent(n):
            if k in wide and (n, k) < a:
                return False
    return True


def firm(bk, c):
    off = set(bk.gone)
    todo = [w for w in reversed(bk.watch) if w not in bk.filed]
    cells = set()
    while todo:
        again = []
        gained = False
        for w in todo:
            d = bk.find(w)
            if d in cells or set(bk.held(d)) & off:
                cells.add(d)
                continue
            if sound(bk, d, off):
                cells.add(d)
                off = off | set(bk.held(d))
                gained = True
            else:
                again.append(w)
        if not gained:
            break
        todo = again
    return c in cells
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
    "ok-settle-by-rounds": {"hold.py": HOLD_ROUNDS},
}

NOTE = {
    "ok-frontier-order": "The group search walks its frontier the other way round.",
    "ok-group-of-keys": "The group search carried over keys instead of cells.",
    "ok-reach-inline": "The reach search folded into the readiness test, so the\n"
                       "declared rch.py is never called. It is here to prove the\n"
                       "interpreter's tallies are floors and not equalities.",
    "ok-settle-by-rounds": "The tick's set of rows grown by a worklist over cells\n"
                           "and from the far end of the watch list, rather than by\n"
                           "rescanning it from the front.",
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
