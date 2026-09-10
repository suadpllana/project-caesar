"""Spans and the claims on them.

A span is a stretch of blocks handed out by one allocation; it never splits and never
grows. Every claim that points into one is registered here, twice over: once in `on`, so
the blocks under a range can be tested for a second claim, and once in `by`, a count per
line, so the charge side can be told which lines stand on the span without walking the
claims. Both are needed - `on` answers "may this block be rewritten in place", `by`
answers "is this span exclusive to one line", and neither answers the other's question.
The span also carries what the family questions need - `cover`, a count per line above a
standing line, and `lca`, the deepest line all of them descend from - which the charge side
keeps current from the same two moments.
"""
from store import dev, tally


class Span:
    __slots__ = ("at", "wide", "on", "by", "mask")

    def __init__(self, at, wide):
        self.at = at
        self.wide = wide
        self.on = {}
        self.by = {}
        self.mask = 0


class Claim:
    __slots__ = ("own", "at", "sp", "off", "wide")

    def __init__(self, own, at, sp, off, wide):
        self.own = own
        self.at = at
        self.sp = sp
        self.off = off
        self.wide = wide


def setup(st):
    return None


def add(st, cl):
    sp = cl.sp
    sp.on[cl] = True
    ln = cl.own.line
    seen = sp.by.get(ln, 0)
    sp.by[ln] = seen + 1
    if not seen:
        tally.gain(st, ln, sp)


def rip(st, cl):
    sp = cl.sp
    del sp.on[cl]
    ln = cl.own.line
    left = sp.by[ln] - 1
    if left:
        sp.by[ln] = left
    else:
        del sp.by[ln]
        tally.lose(st, ln, sp)
    return sp


def sweep(st, touched):
    """Give back every span the caller just emptied, once each."""
    rel = 0
    done = set()
    for sp in touched:
        if sp in done:
            continue
        done.add(sp)
        if not sp.on:
            dev.give(st, sp.at, sp.wide)
            rel += sp.wide
    return rel


def doomed(claims):
    """How many blocks the spans under these claims would return if all were ripped."""
    count = {}
    for cl in claims:
        count[cl.sp] = count.get(cl.sp, 0) + 1
    return sum(sp.wide for sp, k in count.items() if k == len(sp.on))


def bare(cl, lo, hi):
    """The stretches of [lo, hi) in span coordinates that no other claim covers."""
    sp = cl.sp
    marks = []
    for other in sp.on:
        if other is cl:
            continue
        a = other.off
        b = a + other.wide
        if b > lo and a < hi:
            marks.append((a if a > lo else lo, b if b < hi else hi))
    if not marks:
        return [(lo, hi)]
    marks.sort()
    out = []
    at = lo
    for a, b in marks:
        if a > at:
            out.append((at, a))
        if b > at:
            at = b
            if at >= hi:
                break
    if at < hi:
        out.append((at, hi))
    return out
