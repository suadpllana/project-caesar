from store import dev


class Span:
    __slots__ = ("at", "wide", "refs")

    def __init__(self, at, wide):
        self.at = at
        self.wide = wide
        self.refs = 0


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
    cl.sp.refs += 1


def rip(st, cl):
    cl.sp.refs -= 1
    return cl.sp


def sweep(st, touched):
    rel = 0
    done = set()
    for sp in touched:
        if sp in done:
            continue
        done.add(sp)
        if not sp.refs:
            dev.give(st, sp.at, sp.wide)
            rel += sp.wide
    return rel


def bare(cl, lo, hi):
    if cl.sp.refs == 1:
        return [(lo, hi)]
    return []
