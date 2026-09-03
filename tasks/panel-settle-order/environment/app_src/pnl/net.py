from pnl import ev


class Net:
    def __init__(self, feeds, gauges, latch, order):
        self.val = {}
        self.kind = {}
        self.ix = {}
        self.expr = dict(gauges)
        self.dep = {}
        self.rdr = {}
        self.lat = tuple(latch)
        for i, n in enumerate(order):
            self.ix[n] = i
            self.rdr[n] = set()
            if n in feeds:
                self.kind[n] = "f"
                self.val[n] = feeds[n]
            else:
                self.kind[n] = "g"
                self.val[n] = 0
                self.dep[n] = set()
        self.roll = tuple(n for n in order if self.kind[n] == "g")

    def fire(self, n):
        seen = set()
        v = ev.run(self.expr[n], self, seen)
        return v, seen
