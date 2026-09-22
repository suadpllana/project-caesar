"""Variant B: one pass into flat parallel arrays, every lookup a direct index."""


class Tab(object):
    def __init__(self, log):
        self.gp, self.gk, self.gn, self.gr = [], [], [], []
        self.rows = {}
        self.oks = {}
        self.sg = {}
        self.cs = {}
        count = {}
        for pos in range(len(log)):
            ev, args = log[pos]
            if ev == "go":
                kind = args[0]
                at = count.get(kind, 0)
                count[kind] = at + 1
                self.rows.setdefault(kind, []).append(len(self.gp))
                self.gp.append(pos)
                self.gk.append(kind)
                self.gn.append(args[1])
                self.gr.append(at)
            elif ev == "ok":
                self.oks.setdefault((args[0], args[1]), []).append((pos, int(args[2])))
            elif ev == "sig":
                self.sg.setdefault(args[0], []).append((pos, int(args[1])))
            elif ev == "ch":
                self.cs.setdefault(args[0], []).append((pos, int(args[1])))

    def slot(self, kind, i):
        row = self.rows.get(kind)
        if row is None or i >= len(row):
            return None
        at = row[i]
        return self.gp[at], self.gn[at]

    def answer(self, kind, name, j):
        row = self.oks.get((kind, name))
        if row is None or j >= len(row):
            return None
        return row[j]

    def signal(self, tag, j):
        row = self.sg.get(tag)
        if row is None or j >= len(row):
            return None
        return row[j]

    def choice(self, key, j):
        row = self.cs.get(key)
        if row is None or j >= len(row):
            return None
        return row[j]

    def issued(self):
        return [(self.gp[at], self.gk[at], self.gr[at]) for at in range(len(self.gp))]

    def spot(self, pos):
        return pos

    def count(self):
        return len(self.gp)

    def where(self, at):
        return self.gk[at], self.gr[at]

    def order(self):
        return self.gp
