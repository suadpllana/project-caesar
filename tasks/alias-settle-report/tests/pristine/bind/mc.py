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
            if who not in bk.live or a in bk.gone or b in bk.gone:
                return
            bk.weld(a, b)
            self.ev(("ty", self.t, who, a, b))
        elif kind == "bar":
            if who not in bk.live or a in bk.gone or b in bk.gone:
                return
            bk.bars.add((min(a, b), max(a, b)))
            self.ev(("br", self.t, who, a, b))
        elif kind == "shut":
            bk.live.discard(who)
            self.ev(("sd", self.t, who))

    def sweep(self):
        bk = self.bk
        ripe = [w for w in bk.watch
                if w not in bk.filed and hold.firm(bk, bk.find(w))]
        lines = []
        for w in seq.queue(bk, ripe):
            c = bk.find(w)
            rep, sc = card.card(bk, c)
            lines.append((w, c, rep, sc))
        for w, c, rep, sc in lines:
            bk.filed.add(w)
            bk.drop(c)
            self.ev(("fl", self.t, w, rep, sc))

    def run(self):
        for kind, who, a, b in self.sp.script:
            self.t += 1
            self.step(kind, who, a, b)
            self.sweep()
        self.ev(("ed", self.t))
        return self.bk
