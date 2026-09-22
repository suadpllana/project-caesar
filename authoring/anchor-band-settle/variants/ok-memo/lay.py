"""A correct variant: layout kept in dictionaries and per-frame memo tables. Never ships.

Written from the contract, not from the reference. Heights live in a dict and are repaired
after each frame by recomputing every edited box and every box above one from its children,
deepest first; nothing is pushed up as a difference. Row offsets and tops are memo tables that
are thrown away whenever the tree changes and refilled on demand.
"""
from bisect import bisect_right


def depth(b):
    n = 0
    while b.par is not None:
        b = b.par
        n += 1
    return n


def contribution(v, b):
    return 0 if b.lift else v.mh[b]


def remeasure(v, b):
    h = b.own
    if not b.shut:
        for k in b.kids:
            h += contribution(v, k)
    v.mh[b] = h


def start(v):
    v.mh = {}

    def walk(b):
        for k in b.kids:
            walk(k)
        remeasure(v, b)

    for b in v.kids:
        walk(b)
    v.pins_max = max([b.pin for b in v.box.values() if b.pin is not None] or [0])
    forget(v)


def forget(v):
    v.mo = {}
    v.mt = {}


def repair(v):
    """After a frame's edits: remeasure what was edited and everything above it."""
    todo = set()
    for kind, b, arg in v.log:
        if kind == "to":
            continue
        if kind in ("pin", "add") and b.pin is not None:
            v.pins_max = max(v.pins_max, b.pin)
        start_at = b.par if kind == "drop" else b
        x = start_at
        while x is not None:
            todo.add(x)
            x = x.par
        if kind == "add":
            v.mh.setdefault(b, b.own)
    live = [b for b in todo if not b.gone]
    for b in sorted(live, key=depth, reverse=True):
        remeasure(v, b)
    forget(v)


def doc_height(v):
    return sum(contribution(v, b) for b in v.kids)


def offsets(v, owner):
    """Running starts of owner's children, relative to where its children begin."""
    got = v.mo.get(owner)
    if got is None:
        kids = v.kids if owner is None else owner.kids
        at, run, index = [], 0, {}
        for i, k in enumerate(kids):
            at.append(run)
            index[k] = i
            run += contribution(v, k)
        got = (at, index, run)
        v.mo[owner] = got
    return got


def begin(v, owner):
    return 0 if owner is None else top(v, owner) + owner.own


def top(v, b):
    got = v.mt.get(b)
    if got is None:
        at, index, _run = offsets(v, b.par)
        got = begin(v, b.par) + at[index[b]]
        v.mt[b] = got
    return got


def height(v, b):
    return v.mh[b]


def first_reaching(v, owner, line):
    """Index of the first child whose bottom lies below `line`."""
    at, _index, run = offsets(v, owner)
    kids = v.kids if owner is None else owner.kids
    base = begin(v, owner)
    ends = [a + contribution(v, k) for a, k in zip(at, kids)]
    return bisect_right(ends, line - base), base


def in_flow(b):
    if b.gone or b.lift:
        return False
    p = b.par
    while p is not None:
        if p.lift or p.shut:
            return False
        p = p.par
    return True
