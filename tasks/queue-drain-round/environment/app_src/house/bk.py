class Ob:
    __slots__ = ("i", "pr", "pe", "am", "dt", "sq")

    def __init__(self, i, pr, pe, am, dt, sq):
        self.i = i
        self.pr = pr
        self.pe = pe
        self.am = am
        self.dt = dt
        self.sq = sq


OPEN = 0
PAID = 1
GONE = 2


class Book:
    def __init__(self, who, sink):
        self.wh = list(who)
        self.bl = {n: 0 for n in self.wh}
        self.ln = {n: [] for n in self.wh}
        self.ob = {}
        self.stt = {}
        self.at = {}
        self.tk = 0
        self.snk = sink
        self.sq = 0

    def now(self):
        return self.tk

    def roll(self, t):
        self.tk = t

    def who(self):
        return list(self.wh)

    def hold(self, n):
        return self.bl[n]

    def line(self, n):
        return list(self.ln[n])

    def look(self, i):
        return self.ob.get(i)

    def state(self, i):
        return self.stt.get(i, OPEN)

    def book(self, i, pr, pe, am, dt):
        o = Ob(i, pr, pe, am, dt, self.sq)
        self.sq += 1
        self.ob[i] = o
        self.stt[i] = OPEN
        self.ln[pr].append(o)

    def top(self, n, am):
        self.bl[n] += am

    def move(self, plan):
        go = []
        for n in self.wh:
            k = plan.get(n, 0)
            if k <= 0:
                continue
            for o in self.ln[n][:k]:
                go.append(o)
        for o in go:
            self.bl[o.pr] -= o.am
            self.bl[o.pe] += o.am
            self.stt[o.i] = PAID
            self.at[o.i] = self.tk
            self.snk("paid", o.i, self.tk)
        for n in self.wh:
            k = plan.get(n, 0)
            if k > 0:
                self.ln[n] = self.ln[n][k:]
        return len(go)

    def drop(self, i):
        o = self.ob.get(i)
        if o is None or self.stt[i] != OPEN:
            return False
        self.stt[i] = GONE
        self.at[i] = self.tk
        self.ln[o.pr] = [x for x in self.ln[o.pr] if x.i != i]
        self.snk("gone", i, self.tk)
        return True

    def shut(self):
        for n in self.wh:
            self.snk("hold", n, self.bl[n])

    def sheet(self):
        r = {}
        for i in sorted(self.ob):
            s = self.stt[i]
            r[i] = ("open", -1) if s == OPEN else (("paid" if s == PAID else "gone"), self.at[i])
        return r
