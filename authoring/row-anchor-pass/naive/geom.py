"""Naive-but-correct geometry: one flat prefix array, rebuilt whenever a height moves.

This is the shape a first implementation reaches for once the shipped per-call walk is seen to
be slow: keep the item heights in a list, keep a prefix array beside it, rebuild the prefix
array when anything changes and binary search it otherwise. Every answer it gives is the
reference's answer. It is here to be timed, not to be shipped.
"""
import bisect


class Geom:
    __slots__ = ("doc", "kind", "owner", "pos", "pre", "gpos", "ok")

    def __init__(self, doc):
        self.doc = doc
        self.ok = False
        self.build()

    def build(self):
        kind = []
        owner = []
        pos = []
        pre = [0]
        gpos = []
        run = 0
        for gi, g in enumerate(self.doc.gs):
            gpos.append(len(kind))
            kind.append(0)
            owner.append(gi)
            pos.append(-1)
            run += g.hh
            pre.append(run)
            for k, rid in enumerate(g.rows):
                kind.append(1)
                owner.append(gi)
                pos.append(k)
                run += self.doc.rh(g, rid)
                pre.append(run)
        self.kind = kind
        self.owner = owner
        self.pos = pos
        self.pre = pre
        self.gpos = gpos
        self.ok = True

    def _fresh(self):
        if not self.ok:
            self.build()

    def ngroups(self):
        return len(self.doc.gs)

    def ggid(self, gi):
        return self.doc.gs[gi].gid

    def ghh(self, gi):
        return self.doc.gs[gi].hh

    def gindex(self, gid):
        for gi, g in enumerate(self.doc.gs):
            if g.gid == gid:
                return gi
        return -1

    def gtop(self, gi):
        self._fresh()
        return self.pre[self.gpos[gi]]

    def gbase(self, gi):
        self._fresh()
        return self.gpos[gi]

    def count(self):
        self._fresh()
        return len(self.kind)

    def total(self):
        self._fresh()
        return self.pre[-1]

    def height(self, i):
        self._fresh()
        return self.pre[i + 1] - self.pre[i]

    def top(self, i):
        self._fresh()
        return self.pre[i]

    def at(self, y):
        self._fresh()
        if y >= self.pre[-1]:
            return len(self.kind) - 1
        return bisect.bisect_right(self.pre, y) - 1

    def key(self, i):
        self._fresh()
        g = self.doc.gs[self.owner[i]]
        if self.kind[i] == 0:
            return "H%d" % g.gid
        return "R%d" % g.rows[self.pos[i]]

    def mark(self, i):
        self._fresh()
        if self.kind[i] == 0:
            return 0
        g = self.doc.gs[self.owner[i]]
        got = self.doc.mark(g, g.rows[self.pos[i]])
        if got:
            self.ok = False
        return got

    def ins(self, gid, pos, n):
        g = self.doc.byid[gid]
        g.rows[pos:pos] = self.doc.fresh(g, n)
        self.ok = False

    def dele(self, gid, pos, n):
        g = self.doc.byid[gid]
        del g.rows[pos:pos + n]
        self.ok = False
