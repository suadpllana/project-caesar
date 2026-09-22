#!/bin/bash
# the holder is resolved once, at the old offset, for every pass
set -euo pipefail

cat > /app/view/lay.py <<'PYEOF'
from itertools import accumulate


def build(v):
    v.tops = {}
    v.tmax = 0
    v.ends = None
    v.idx = None
    v.ks = 0
    for b in v.kids:
        v.ks += settle(v, b)


def settle(v, b):
    """Compute the caches of a whole subtree bottom-up; return its flow contribution."""
    ks = 0
    for c in b.kids:
        ks += settle(v, c)
    b.ks = ks
    b.hh = b.own + (0 if b.shut else ks)
    b.cf = 0 if b.lift else b.hh
    b.ends = None
    b.idx = None
    if b.pin is not None and b.pin > v.tmax:
        v.tmax = b.pin
    return b.cf


def spoil(v, p, index=False):
    """p's row is stale: its running ends always, its index map too when the row changed."""
    o = v if p is None else p
    o.ends = None
    if index:
        o.idx = None


def bump(v, p, d):
    """A child of p now counts d more than it did; carry that up while it changes anything."""
    while p is not None:
        p.ks += d
        p.ends = None
        p.hh = p.own + (0 if p.shut else p.ks)
        new = 0 if p.lift else p.hh
        d = new - p.cf
        p.cf = new
        if d == 0:
            return
        p = p.par
    v.ks += d
    v.ends = None


def touch(v, b):
    b.hh = b.own + (0 if b.shut else b.ks)
    new = 0 if b.lift else b.hh
    d = new - b.cf
    b.cf = new
    if d:
        spoil(v, b.par)
        bump(v, b.par, d)


def sync(v):
    """Bring the caches up to the tree after a frame's edits."""
    for kind, b, arg in v.log:
        if kind == "to":
            continue
        if kind == "add":
            b.ks = 0
            b.hh = b.own
            b.cf = 0
            b.ends = None
            b.idx = None
            if b.pin is not None and b.pin > v.tmax:
                v.tmax = b.pin
            spoil(v, b.par, index=True)
            touch(v, b)
        elif kind == "drop":
            spoil(v, b.par, index=True)
            d = -b.cf
            b.cf = 0
            if d:
                bump(v, b.par, d)
        elif kind in ("pin", "unpin"):
            if b.pin is not None and b.pin > v.tmax:
                v.tmax = b.pin
            spoil(v, b.par, index=True)
        else:
            touch(v, b)
    v.tops = {}


def row(v, p):
    """(running ends, index of each child, indices of pinned children) for p's children."""
    o = v if p is None else p
    kids = o.kids
    if o.idx is None:
        o.idx = ({c: i for i, c in enumerate(kids)},
                 [i for i, c in enumerate(kids) if c.pin is not None])
    if o.ends is None:
        o.ends = list(accumulate(c.cf for c in kids))
    return o.ends, o.idx[0], o.idx[1]


def base(v, p):
    """Where p's children start: its top plus its own height, or 0 for the top level."""
    if p is None:
        return 0
    return top(v, p) + p.own


def top(v, b):
    y = v.tops.get(b)
    if y is None:
        p = b.par
        ends, at, _ = row(v, p)
        y = base(v, p) + ends[at[b]] - b.cf
        v.tops[b] = y
    return y


def laid(b):
    """In the flow and not hidden: nothing lifted from it upward, nothing shut above it."""
    if b.gone or b.lift:
        return False
    p = b.par
    while p is not None:
        if p.lift or p.shut:
            return False
        p = p.par
    return True


def end_of_section(v, b):
    if b.par is None:
        return v.ks
    return top(v, b.par) + b.par.hh


def span(v):
    return max(0, v.ks - v.vh)


def in_live(b):
    x = b
    while x is not None:
        if x.live:
            return True
        x = x.par
    return False
PYEOF

cat > /app/view/stick.py <<'PYEOF'
from bisect import bisect_right

from view import lay


def drawn(v, b, s):
    """Where a pinned box is drawn at offset s when it is stuck there, else None."""
    if b.pin is None or b.hh <= 0:
        return None
    r = min(s + b.pin, lay.end_of_section(v, b) - b.hh)
    if r > lay.top(v, b):
        return r
    return None


def stuck_in(v, b, s):
    """b or a box above it is stuck at s. b must be laid out."""
    x = b
    while x is not None:
        if x.pin is not None and drawn(v, x, s) is not None:
            return True
        x = x.par
    return False


def band(v, s):
    """The lowest bottom edge of a stuck header, measured from the top of the view."""
    lo, hi = s, s + v.tmax
    best = 0
    todo = [None]
    while todo:
        p = todo.pop()
        kids = v.kids if p is None else p.kids
        ends, _at, pins = lay.row(v, p)
        start = lay.base(v, p)
        for i in pins:
            c = kids[i]
            if c.lift or c.hh <= 0:
                continue
            if start + ends[i] - c.cf >= hi:
                break
            r = drawn(v, c, s)
            if r is not None and r + c.hh - s > best:
                best = r + c.hh - s
        j = bisect_right(ends, lo - start)
        while j < len(kids):
            c = kids[j]
            y = start + ends[j] - c.cf
            if y >= hi:
                break
            if c.cf > 0 and not c.shut:
                todo.append(c)
            j += 1
    return best
PYEOF

cat > /app/view/pick.py <<'PYEOF'
from bisect import bisect_right

from view import lay, stick


def first(v, s, band):
    u, w = s + band, s + v.vh
    if u >= w:
        return None

    def look(p):
        kids = v.kids if p is None else p.kids
        ends, _at, _pins = lay.row(v, p)
        start = lay.base(v, p)
        j = bisect_right(ends, u - start)
        while j < len(kids):
            c = kids[j]
            y = start + ends[j] - c.cf
            if y >= w:
                return None
            j += 1
            if c.cf == 0 or c.live:
                continue
            if c.pin is not None and stick.drawn(v, c, s) is not None:
                continue
            e = y + c.hh
            if y >= u and e <= w:
                return c
            if not c.shut:
                got = look(c)
                if got is not None:
                    return got
            return c
        return None

    return look(None)
PYEOF

cat > /app/view/hold.py <<'PYEOF'
from view import lay, pick, stick


def start(v):
    lay.build(v)
    v.chain = None


def before(v):
    s = v.s
    band = stick.band(v, s)
    got = pick.first(v, s, band)
    if got is None:
        v.chain = None
        return
    u = s + band
    chain = []
    x = got
    while x is not None:
        chain.append((x, lay.top(v, x) - u))
        x = x.par
    v.chain = chain


def qualifies(v, x, s):
    return lay.laid(x) and x.hh > 0 and not stick.stuck_in(v, x, s)


def after(v):
    ask = None
    live = False
    for kind, b, arg in v.log:
        if kind == "to":
            ask = arg
        elif not live and lay.in_live(b):
            live = True
    lay.sync(v)
    most = lay.span(v)

    def clamp(x):
        return min(max(x, 0), most)

    if ask is not None:
        return clamp(ask), "off scroll"
    if live:
        return clamp(v.s), "off live"
    if v.chain is None:
        return clamp(v.s), "none"
    s = v.s
    seen = []
    held = None
    for x, d in v.chain:
        if qualifies(v, x, s):
            held = (x, d)
            break
    for _ in range(4):
        band = stick.band(v, s)
        if held is None:
            return clamp(s), "none"
        x, d = held
        want = clamp(lay.top(v, x) - d - band)
        if want == s:
            return s, x.id
        seen.append((want, x))
        s = want
    best = min(want for want, _x in seen)
    for want, x in seen:
        if want == best:
            return want, x.id
    raise AssertionError("four passes and no offset")
PYEOF

