LW = 4


class Mem:
    def __init__(self, init):
        self.gm = dict(init)
        self.held = []

    def word(self, a):
        return self.gm.get(a, 0)

    def fetch(self, ln):
        return [self.word(ln * LW + i) for i in range(LW)]

    def ld(self, blk, a, cached):
        if not cached:
            return self.word(a)
        ln = a // LW
        row = blk.l1.get(ln)
        if row is None:
            row = self.fetch(ln)
            blk.l1.put(ln, row)
        return row[a % LW]

    def st(self, blk, a, v):
        self.gm[a] = v
        self.sync(a)

    def add(self, blk, a, v):
        old = self.word(a)
        self.gm[a] = old + v
        self.sync(a)
        return old

    def sync(self, a):
        ln = a // LW
        for l1 in self.held:
            if l1.has(ln):
                l1.rows[ln][a % LW] = self.gm[a]

    def fence(self, blk):
        pass
