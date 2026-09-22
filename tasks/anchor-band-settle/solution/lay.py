"""Flow layout kept current from the tree's change log instead of rebuilt per frame.

Flow layout has one property that makes this cheap: an edit changes heights only along the
edited box's ancestor chain, and a box's top is its parent's top, plus the parent's own height,
plus the flow heights of the siblings before it. So every box carries three cached numbers - the
flow height of its children (`ks`), its own flow height (`hh`) and what its parent currently
counts for it (`cf`, zero while it is lifted) - and every row of children carries its running
ends, rebuilt only when a child's contribution changed, and its index map with the positions of
its pinned children, rebuilt only when the row itself or a child's pin changed. Tops are
computed on demand from those rows and memoised until the next edit.

Every touch recomputes a box's numbers from the tree as it stands and pushes the difference
from what its parent counted, so the order the log is replayed in cannot leave the caches out
of step with the tree: a later edit in the same frame has already happened by the time an
earlier one is replayed, and replaying it again finds nothing left to move.
"""
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
