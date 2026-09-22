MIX = 2654435761


class Grp:
    __slots__ = ("gid", "hh", "lo", "hi", "rows")

    def __init__(self, gid, hh, lo, hi):
        self.gid = gid
        self.hh = hh
        self.lo = lo
        self.hi = hi
        self.rows = []


class Doc:
    __slots__ = ("gs", "byid", "nxt")

    def __init__(self, decls):
        self.gs = []
        self.byid = {}
        self.nxt = 0
        for gid, hh, lo, hi, n in decls:
            g = Grp(gid, hh, lo, hi)
            self.gs.append(g)
            self.byid[gid] = g
            g.rows.extend(self.fresh(g, n))

    def fresh(self, g, n):
        out = list(range(self.nxt, self.nxt + n))
        self.nxt += n
        return out

    def real(self, g, rid):
        return g.lo + (rid * MIX) % (g.hi - g.lo + 1)
