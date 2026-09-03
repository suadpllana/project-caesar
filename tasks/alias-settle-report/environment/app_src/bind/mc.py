from bind import card, hold, seq
from bind.bk import Book


class Mach(object):
    def __init__(self, sp, sink):
        self.sp = sp
        self.bk = Book(sp)
        self.sink = sink
        self.t = 0

    def ev(self, row):
        self.sink(tuple(row))

    def step(self, kind, who, a, b):
        bk = self.bk
        if kind == "post":
            bk.post[(who, a)] = b
            self.ev(("ps", self.t, who, a, b))
        elif kind == "tie":
            bk.weld(a, b)
            self.ev(("ty", self.t, who, a, b))
        elif kind == "bar":
            bk.bars.add((min(a, b), max(a, b)))
            self.ev(("br", self.t, who, a, b))
        elif kind == "shut":
            bk.live.discard(who)
            self.ev(("sd", self.t, who))

    def sweep(self):
        bk = self.bk
        ripe = [w for w in bk.watch
                if w not in bk.filed and hold.firm(bk, bk.find(w))]
        for w in seq.queue(bk, ripe):
            rep, sc = card.card(bk, bk.find(w))
            bk.filed.add(w)
            self.ev(("fl", self.t, w, rep, sc))

    def run(self):
        for kind, who, a, b in self.sp.script:
            self.t += 1
            self.step(kind, who, a, b)
            self.sweep()
        self.ev(("ed", self.t))
        return self.bk
