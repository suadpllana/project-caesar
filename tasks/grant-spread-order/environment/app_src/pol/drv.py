import hashlib

from . import graft, spread, weigh
from .store import St

SCOPE = {"h": 0, "b": 1, "d": 2}


class Drv:
    def __init__(self, ops, sink):
        self.ops = ops
        self.sink = sink
        self.st = St()
        self.n = 0

    def ev(self, row):
        self.sink(row)

    def sig(self):
        h = hashlib.sha256()
        for nid in self.st.all():
            up = self.st.up(nid)
            h.update(("|%s^%s^%d" % (nid, up if up else "-",
                                     1 if self.st.stops(nid) else 0)).encode("utf-8"))
            for r in sorted(self.st.held(nid), key=lambda x: x.key()):
                h.update((";%s,%d,%d,%d,%s,%d" % (r.sb, r.rt, r.vd, r.sc, r.og, r.bn)).encode("utf-8"))
        for g in self.st.crews():
            h.update(("&%s:%s" % (g, ",".join(sorted(self.st.mems(g))))).encode("utf-8"))
        return h.hexdigest()[:16]

    def step(self, op):
        k = op[0]
        if k == "nd":
            graft.sprout(self.st, op[1], None if op[2] == "-" else op[2], self.n)
            self.ev(["nd", self.n, op[1], op[2]])
        elif k == "st":
            vd = 1 if op[4] == "a" else 0
            sc = SCOPE[op[5]]
            spread.plant(self.st, op[1], op[2], int(op[3]), vd, sc, self.n)
            self.ev(["st", self.n, op[1], op[2], int(op[3]), vd, sc])
        elif k == "cl":
            spread.pull(self.st, op[1], op[2], int(op[3]), self.n)
            self.ev(["cl", self.n, op[1], op[2], int(op[3])])
        elif k == "mv":
            graft.move(self.st, op[1], op[2], self.n)
            self.ev(["mv", self.n, op[1], op[2]])
        elif k == "sl":
            graft.shut(self.st, op[1], self.n)
            self.ev(["sl", self.n, op[1]])
        elif k == "us":
            graft.free(self.st, op[1], self.n)
            self.ev(["us", self.n, op[1]])
        elif k == "mb":
            if op[3] == "+":
                self.st.join(op[1], op[2])
            else:
                self.st.part(op[1], op[2])
            self.ev(["mb", self.n, op[1], op[2], op[3]])
        elif k == "ak":
            r = weigh.pick(self.st, op[1], op[2], int(op[3]))
            if r is None:
                self.ev(["ak", self.n, op[1], op[2], int(op[3]), 0, "-", "-", -1, -1])
            else:
                self.ev(["ak", self.n, op[1], op[2], int(op[3]),
                         int(r.vd), r.sb, r.og, int(r.bn), int(r.sc)])
        else:
            raise ValueError(k)

    def go(self):
        for op in self.ops:
            self.n += 1
            self.step(op)
            self.ev(["dg", self.n, self.sig()])
        for nid in self.st.all():
            up = self.st.up(nid)
            self.ev(["fin", nid, up if up else "-", 1 if self.st.stops(nid) else 0,
                     [[r.sb, r.rt, r.vd, r.sc, r.og, r.bn]
                      for r in sorted(self.st.held(nid), key=lambda x: x.key())]])
        for g in self.st.crews():
            self.ev(["crew", g, sorted(self.st.mems(g))])
