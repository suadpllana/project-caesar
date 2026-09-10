"""Spans and the claims on them.

A span is a stretch of blocks handed out by one allocation; it never splits and never
grows. Every claim that points into one is registered here, twice over: once in `on`, so
the blocks under a range can be tested for a second claim, and once in `by`, a count per
line, so the charge side can be told which lines stand on the span without walking the
claims. Both are needed - `on` answers "may this block be rewritten in place", `by`
answers "is this span exclusive to one line", and neither answers the other's question.
"""
from store import dev, tally


class Span:
    __slots__ = ("at", "wide", "on", "by")

    def __init__(self, at, wide):
        self.at = at
        self.wide = wide
        self.on = {}
        self.by = {}


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
    seen = sp.by.get(cl.own.line, 0)
    sp.by[cl.own.line] = seen + 1
    if not seen:
        tally.gain(st, cl.own.line, sp)


def rip(st, cl):
    sp = cl.sp
    del sp.on[cl]
    left = sp.by[cl.own.line] - 1
    if left:
        sp.by[cl.own.line] = left
    else:
        del sp.by[cl.own.line]
        tally.lose(st, cl.own.line, sp)
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
    """The stretches of [lo, hi) no other claim covers, marked off block by block."""
    sp = cl.sp
    seen = [False] * (hi - lo)
    for other in sp.on:
        if other is cl:
            continue
        a = other.off
        b = a + other.wide
        if b <= lo or a >= hi:
            continue
        for k in range(max(a, lo) - lo, min(b, hi) - lo):
            seen[k] = True
    out = []
    open_at = None
    for k, taken in enumerate(seen):
        if taken:
            if open_at is not None:
                out.append((open_at, lo + k))
                open_at = None
        elif open_at is None:
            open_at = lo + k
    if open_at is not None:
        out.append((open_at, hi))
    return out
