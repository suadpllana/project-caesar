class Geom:
    __slots__ = ("doc",)

    def __init__(self, doc):
        self.doc = doc

    def ngroups(self):
        return len(self.doc.gs)

    def ggid(self, gi):
        return self.doc.gs[gi].gid

    def ghh(self, gi):
        return self.doc.gs[gi].hh

    def gtop(self, gi):
        y = 0
        for g in self.doc.gs[:gi]:
            y += g.hh
            for rid in g.rows:
                y += self.doc.rh(g, rid)
        return y

    def count(self):
        i = 0
        for g in self.doc.gs:
            i += 1 + len(g.rows)
        return i

    def total(self):
        y = 0
        for g in self.doc.gs:
            y += g.hh
            for rid in g.rows:
                y += self.doc.rh(g, rid)
        return y

    def _place(self, i):
        for g in self.doc.gs:
            if i == 0:
                return g, -1
            i -= 1
            if i < len(g.rows):
                return g, i
            i -= len(g.rows)
        return None, -1

    def top(self, i):
        y = 0
        for g in self.doc.gs:
            if i == 0:
                return y
            y += g.hh
            i -= 1
            if i < len(g.rows):
                for rid in g.rows[:i]:
                    y += self.doc.rh(g, rid)
                return y
            for rid in g.rows:
                y += self.doc.rh(g, rid)
            i -= len(g.rows)
        return y

    def at(self, y):
        i = 0
        run = 0
        for g in self.doc.gs:
            if run + g.hh > y:
                return i
            run += g.hh
            i += 1
            for rid in g.rows:
                h = self.doc.rh(g, rid)
                if run + h > y:
                    return i
                run += h
                i += 1
        return i - 1

    def key(self, i):
        g, k = self._place(i)
        if k < 0:
            return "H%d" % g.gid
        return "R%d" % g.rows[k]

    def mark(self, i):
        g, k = self._place(i)
        if k < 0:
            return 0
        return self.doc.mark(g, g.rows[k])

    def ins(self, gid, pos, n):
        g = self.doc.byid[gid]
        g.rows[pos:pos] = self.doc.fresh(g, n)

    def dele(self, gid, pos, n):
        g = self.doc.byid[gid]
        del g.rows[pos:pos + n]
