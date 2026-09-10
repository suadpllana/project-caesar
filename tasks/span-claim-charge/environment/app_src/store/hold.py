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


def bare(cl, lo, hi):
    if len(cl.sp.on) == 1:
        return [(lo, hi)]
    return []
