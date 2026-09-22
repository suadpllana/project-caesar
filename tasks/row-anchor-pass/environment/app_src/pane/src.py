MIX = 2654435761


class Grp:
    __slots__ = ("gid", "hh", "est", "lo", "hi", "rows")

    def __init__(self, gid, hh, est, lo, hi):
        self.gid = gid
        self.hh = hh
        self.est = est
        self.lo = lo
        self.hi = hi
        self.rows = []


class Doc:
    __slots__ = ("gs", "byid", "seen", "nxt", "meas")

    def __init__(self, decls):
        self.gs = []
        self.byid = {}
        self.seen = {}
        self.nxt = 0
        self.meas = 0
        for gid, hh, est, lo, hi, n in decls:
            g = Grp(gid, hh, est, lo, hi)
            self.gs.append(g)
            self.byid[gid] = g
            g.rows.extend(self.fresh(g, n))

    def fresh(self, g, n):
        out = list(range(self.nxt, self.nxt + n))
        self.nxt += n
        return out

    def real(self, g, rid):
        return g.lo + (rid * MIX) % (g.hi - g.lo + 1)

    def rh(self, g, rid):
        h = self.seen.get(rid)
        return g.est if h is None else h

    def mark(self, g, rid):
        if rid in self.seen:
            return 0
        self.seen[rid] = self.real(g, rid)
        self.meas += 1
        return 1
