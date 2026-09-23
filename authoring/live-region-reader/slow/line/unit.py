"""Where a difference sits: what holds it, and which unit it is spoken as.

Both questions start from one element. For an addition or a text change it is the node's parent
now. For a removal the node is nowhere now, so it is the anchor - the parent the node had when
the listener last believed it - provided that anchor is still exposed in the same region; if not,
the removal sits at its region element alone. The removal is placed where it was last believed,
not where anything is now, and moves inside a region never refresh that.

Holds read every element from the start up to and including the region element: one
`aria-busy="true"` among them holds the difference. Units walk the same path and stop at the
first element whose `aria-atomic` is `true` or `false`: `true` makes that element the unit,
`false` means the difference is spoken alone, and reaching the region element without either
means alone as well. A removal with no start element is always spoken alone.
"""
from . import look


def start(pg, know, k, cur):
    r, _n = k
    if cur is not None:
        return cur[1]
    a = know.expect(k)[1]
    shown, reg = look.place(pg, a)
    if shown and reg == r:
        return a
    return None


def held(pg, know, k, cur):
    r, _n = k
    s = start(pg, know, k, cur)
    x = r if s is None else s
    while True:
        if look.busy(pg, x):
            return True
        if x == r:
            return False
        x = pg.up(x)


def unit(pg, know, k, cur):
    r, _n = k
    s = start(pg, know, k, cur)
    if s is None:
        return None
    x = s
    while True:
        v = look.atomic(pg, x)
        if v == "true":
            return x
        if v == "false" or x == r:
            return None
        x = pg.up(x)


def read(pg, u):
    """The exposed text nodes and elements inside u, in document order."""
    texts, els = [], []
    todo = [u]
    while todo:
        x = todo.pop()
        if pg.is_text(x):
            texts.append(x)
            continue
        if look.hides(pg, x):
            continue
        els.append(x)
        todo.extend(reversed(pg.kids(x)))
    return texts, els
