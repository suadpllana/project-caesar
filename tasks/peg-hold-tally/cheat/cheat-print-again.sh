#!/bin/bash
# prints a block that has already been given back at every later trim
set -euo pipefail

cat > /app/keep/live.py <<'PYEOF'
"""What a volume holds, for how long, and what that leaves behind.

A volume's hold on one block is an episode: it opens when the first slot of that volume takes the
block and closes when the last one lets it go. A block may be held at several slots of one volume
at once, and may be taken back after it has left, so a block has a series of episodes per volume
rather than one stretch of time.

A closed episode leaves a run: the pegs of that volume whose stamps fall inside it. What has to be
known about a run is only whether it stands for no keeper, one keeper or more, so a run carries the
two youngest living pegs it covers. No keeper means the run is gone; one keeper means the second of
the two is missing. Both change only when one of those two pegs is shed, which is what keeps a shed
off every run that merely contains it.
"""
from keep import cover

B, V, T1, T2, HI, PEN, OK = range(7)


class Acct:
    def __init__(self):
        self.t = 0
        self.roll = []
        self.made = {}
        self.hn = {}
        self.op = {}
        self.nh = {}
        self.rs = {}
        self.sof = {}
        self.sole = {}
        self.stop = {}
        self.fresh = []
        self.q = []
        self.out = set()
        self.pt = {}
        self.pn = {}
        self.nf = {}
        self.pf = {}
        self.home = {}
        self.hi_at = {}
        self.pen_at = {}


def new():
    return Acct()


def born(a, b, t):
    a.t = t
    a.roll.append(b)
    a.made[b] = t
    a.nh[b] = 0
    a.rs[b] = []


def hold(a, v, x, b, t):
    a.t = t
    k = (b, v)
    n = a.hn.get(k, 0)
    if n == 0:
        a.op[k] = t
        a.nh[b] += 1
        if a.nh[b] == 1:
            touch(a, b, t)
    a.hn[k] = n + 1


def free(a, v, x, b, t):
    a.t = t
    k = (b, v)
    n = a.hn[k] - 1
    if n:
        a.hn[k] = n
        return
    del a.hn[k]
    shut(a, b, v, a.op.pop(k), t)
    a.nh[b] -= 1
    touch(a, b, t)
    flush(a)


def shut(a, b, v, t1, t2):
    """File the run this closed episode leaves under the two youngest pegs it covers."""
    hi = cover.last(a, v, t1, t2)
    if hi is None:
        return
    r = [b, v, t1, t2, hi, cover.under(a, v, hi, t1), True]
    a.rs[b].append(r)
    file(a, r)


def file(a, r):
    a.hi_at.setdefault(a.pn[r[V]][r[HI]], []).append(r)
    if r[PEN] is not None:
        a.pen_at.setdefault(a.pn[r[V]][r[PEN]], []).append(r)


def kill(a, r):
    r[OK] = False
    a.rs[r[B]].remove(r)


def touch(a, b, t):
    """Settle whether the block is kept at all, and whether one peg alone keeps it."""
    rs = a.rs[b]
    held = a.nh[b]
    if not held and not rs and b not in a.stop:
        a.stop[b] = t
        a.fresh.append(b)
    one = None
    if not held and len(rs) == 1 and rs[0][PEN] is None:
        r = rs[0]
        one = a.pn[r[V]][r[HI]]
    was = a.sof.get(b)
    if was != one:
        if was is not None:
            a.sole[was] -= 1
        if one is not None:
            a.sole[one] = a.sole.get(one, 0) + 1
        a.sof[b] = one


def flush(a):
    """Blocks that stopped being kept during one op join the queue in allocation order."""
    if a.fresh:
        a.fresh.sort()
        a.q.extend(a.fresh)
        del a.fresh[:]
PYEOF

cat > /app/keep/cover.py <<'PYEOF'
"""Pegs, per volume, and the pegs a closed episode covers.

A peg is made in constant time: it records only its volume and its stamp. Which blocks it keeps is
settled afterwards, when a volume lets a block go, because a volume's hold on one block runs from
the stamp it took it to the stamp it let it go, and the pegs of that volume that keep the block are
exactly those whose stamps fall inside that run.

The skip list answers "the last living peg at or before this index" after any number of sheds, so
neither closing an episode nor shedding a peg walks a volume's peg list.
"""
import bisect


def pegged(a, p, v, t):
    a.t = t
    pt = a.pt.setdefault(v, [])
    a.pn.setdefault(v, []).append(p)
    a.pf.setdefault(v, [0]).append(len(pt) + 1)
    a.home[p] = (v, len(pt))
    pt.append(t)


def pv(a, v, i):
    """The largest living peg index of v at or before i, or None."""
    if i < 0:
        return None
    f = a.pf[v]
    r = i + 1
    while f[r] != r:
        r = f[r]
    j = i + 1
    while f[j] != r:
        f[j], j = r, f[j]
    return r - 1 if r > 0 else None


def sink(a, v, i):
    """Take peg index i of v out of the skip list."""
    a.pf[v][i + 1] = i


def last(a, v, t1, t2):
    """The youngest living peg of v with a stamp in [t1, t2), as an index, or None."""
    pt = a.pt.get(v)
    if not pt:
        return None
    i = pv(a, v, bisect.bisect_left(pt, t2) - 1)
    return None if i is None or pt[i] < t1 else i


def under(a, v, i, t1):
    """The living peg of v just below index i, still at or after t1, or None."""
    j = pv(a, v, i - 1)
    return None if j is None or a.pt[v][j] < t1 else j
PYEOF

cat > /app/keep/edge.py <<'PYEOF'
"""Shedding a peg.

Only the runs that carry the shed peg as one of their two youngest keepers change: a run that
merely contains it still has two younger living pegs above it, so it still stands for two keepers
or more and nothing about it has to be recomputed. That is why a shed costs the peg's two buckets
rather than a pass over the blocks.
"""
from keep import cover, live


def shed(a, p, t):
    a.t = t
    v, i = a.home.pop(p)
    cover.sink(a, v, i)
    hurt = []
    for r in a.hi_at.pop(p, ()):
        if not r[live.OK] or a.pn[r[live.V]][r[live.HI]] != p:
            continue
        w = r[live.V]
        j = cover.under(a, w, i, r[live.T1])
        if j is None:
            live.kill(a, r)
        else:
            r[live.HI] = j
            r[live.PEN] = cover.under(a, w, j, r[live.T1])
            live.file(a, r)
        hurt.append(r[live.B])
    for r in a.pen_at.pop(p, ()):
        if not r[live.OK] or r[live.PEN] is None or a.pn[r[live.V]][r[live.PEN]] != p:
            continue
        w = r[live.V]
        r[live.PEN] = cover.under(a, w, i, r[live.T1])
        if r[live.PEN] is not None:
            a.pen_at.setdefault(a.pn[w][r[live.PEN]], []).append(r)
        hurt.append(r[live.B])
    for b in sorted(set(hurt)):
        live.touch(a, b, t)
    live.flush(a)
PYEOF

cat > /app/keep/gone.py <<'PYEOF'
"""The trim.

A block that stops being kept is queued the moment it happens, so the list a trim prints is
already in the order they stopped, with the blocks of any one op in allocation order. Once
printed a block is never queued again, because it can never be kept again: taking a block back
into a volume needs a peg that still keeps it.
"""


def trim(a, t):
    a.t = t
    a.out.update(a.q)
    return list(a.q)
PYEOF

cat > /app/keep/sole.py <<'PYEOF'
"""The tally.

Carried, not counted: a block joins one peg's tally when it comes to have one run whose ends
coincide and no volume holding it, and leaves again when either changes.
"""


def count(a, p):
    return a.sole.get(p, 0)
PYEOF
