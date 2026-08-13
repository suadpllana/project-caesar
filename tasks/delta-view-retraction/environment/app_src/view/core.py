from store import agg


class Cell:
    __slots__ = ("g", "kind", "acc", "dep")

    def __init__(self, g, kind):
        self.g = g
        self.kind = kind
        self.acc = agg.blank(kind)
        self.dep = {}

    def copy(self):
        c = Cell(self.g, self.kind)
        c.acc = self.acc.copy()
        c.dep = dict(self.dep)
        return c


class Core:
    def __init__(self, spec):
        self.spec = spec
        self.cells = {}
        self.folds = 0
        self.scans = 0
        self.emits = 0
        self.log = []
        self.jrn = []
        self.tk = 0

    def tick(self, seq):
        self.tk = seq

    def cell(self, g, kind):
        c = self.cells.get((g, kind))
        if c is None:
            c = Cell(g, kind)
            self.cells[(g, kind)] = c
        return c

    def apply(self, g, kind, v, w, rk):
        c = self.cell(g, kind)
        agg.fold(c.acc, v, w)
        self.folds += 1
        self.jrn.append(("f", self.tk, g, kind, v, w))
        d = c.dep.get(rk, 0) + w
        if d == 0:
            c.dep.pop(rk, None)
        else:
            c.dep[rk] = d
        return c

    def rebuild(self, g, kind, rws):
        c = Cell(g, kind)
        self.scans += 1
        self.jrn.append(("s", self.tk, g, kind))
        for r in rws:
            agg.fold(c.acc, r.v, r.w)
            self.folds += 1
            self.jrn.append(("f", self.tk, g, kind, r.v, r.w))
            d = c.dep.get(r.key(), 0) + r.w
            if d == 0:
                c.dep.pop(r.key(), None)
            else:
                c.dep[r.key()] = d
        self.cells[(g, kind)] = c
        return c

    def emit(self, g, kind, seq):
        c = self.cells.get((g, kind))
        val = 0 if c is None else agg.value(c.acc)
        self.emits += 1
        self.log.append((seq, g, kind, val))
        self.jrn.append(("e", seq, g, kind, val))
        return val

    def groups(self):
        gs = set()
        for (g, kind) in self.cells:
            gs.add(g)
        return sorted(gs)

    def report(self):
        out = {}
        for (g, kind), c in self.cells.items():
            out["%s|%s" % (g, kind)] = agg.value(c.acc)
        return out
