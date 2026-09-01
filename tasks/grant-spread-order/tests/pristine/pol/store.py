class R:
    __slots__ = ("sb", "rt", "vd", "sc", "og", "bn")

    def __init__(self, sb, rt, vd, sc, og, bn):
        self.sb = sb
        self.rt = rt
        self.vd = vd
        self.sc = sc
        self.og = og
        self.bn = bn

    def key(self):
        return (self.sb, self.rt, self.vd, self.sc, self.og, self.bn)

    def copy(self):
        return R(self.sb, self.rt, self.vd, self.sc, self.og, self.bn)

    def __repr__(self):
        return "R(%s,%d,%s,%d,%s,%d)" % (
            self.sb, self.rt, "a" if self.vd else "d", self.sc, self.og, self.bn)


class St:
    def __init__(self):
        self.pa = {}
        self.kd = {}
        self.bk = set()
        self.hd = {}
        self.gm = {}

    def mk(self, nid, pa):
        self.pa[nid] = pa
        self.kd[nid] = []
        self.hd[nid] = []
        if pa is not None:
            self.kd[pa].append(nid)

    def up(self, nid):
        return self.pa.get(nid)

    def kids(self, nid):
        return list(self.kd.get(nid, ()))

    def line(self, nid):
        out = []
        cur = nid
        while cur is not None and cur in self.pa:
            out.append(cur)
            cur = self.pa[cur]
        return out

    def relink(self, nid, dst):
        old = self.pa.get(nid)
        if old is not None and nid in self.kd.get(old, ()):
            self.kd[old].remove(nid)
        self.pa[nid] = dst
        self.kd[dst].append(nid)

    def held(self, nid):
        return list(self.hd.get(nid, ()))

    def put(self, nid, r):
        self.hd[nid].append(r)

    def rip(self, nid, fn):
        keep = [r for r in self.hd[nid] if not fn(r)]
        gone = len(self.hd[nid]) - len(keep)
        self.hd[nid] = keep
        return gone

    def stops(self, nid):
        return nid in self.bk

    def bar(self, nid, on):
        if on:
            self.bk.add(nid)
        else:
            self.bk.discard(nid)

    def join(self, g, m):
        self.gm.setdefault(g, [])
        if m not in self.gm[g]:
            self.gm[g].append(m)

    def part(self, g, m):
        if g in self.gm and m in self.gm[g]:
            self.gm[g].remove(m)

    def mems(self, g):
        return list(self.gm.get(g, ()))

    def crews(self):
        return sorted(self.gm)

    def all(self):
        return sorted(self.pa)
