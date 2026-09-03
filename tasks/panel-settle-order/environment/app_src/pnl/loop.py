from pnl import net as _net
from pnl import ord as _ord
from pnl import same as _same
from pnl import trip as _trip
from pnl import wire as _wire

STEPS = 60000
TURNS = 60


class Stop(Exception):
    pass


class Loop:
    def __init__(self, feeds, gauges, latch, rounds, order, out):
        self.net = _net.Net(feeds, gauges, latch, order)
        self.rounds = tuple(rounds)
        self.out = out
        self.pl = _ord.start(self.net)
        self.n = 0

    def say(self, rno, tag, name, val):
        self.out((rno, tag, name, val))

    def by(self, names):
        return sorted(names, key=lambda m: self.net.ix[m])

    def spin(self, rno, moved):
        nt = self.net
        while True:
            self.n += 1
            if self.n > STEPS:
                raise Stop("steps")
            g = _ord.take(self.pl, nt)
            if g is None:
                return
            v, seen = nt.fire(g)
            if _wire.tie(self.pl, nt, g, seen):
                _ord.wake(self.pl, nt, g)
                continue
            old = nt.val[g]
            nt.val[g] = v
            self.say(rno, "cp", g, v)
            if _same.moved(old, v):
                moved.add(g)
                for r in self.by(nt.rdr.get(g, ())):
                    _ord.wake(self.pl, nt, r)
            for t in _trip.due(self.pl, nt, "run", rno, g, moved):
                self.pop(rno, t)

    def pop(self, rno, name):
        for nm, tgt, wr in self.net.lat:
            if nm == name:
                self.say(rno, "tr", nm, self.net.val[tgt])
                self.fired.append(nm)
                return

    def build(self):
        nt = self.net
        for g in nt.roll:
            _ord.wake(self.pl, nt, g)
        self.fired = []
        self.spin(0, set())

    def turn(self, rno, writes):
        nt = self.net
        moved = set()
        self.fired = []
        for k, v in writes:
            if nt.kind.get(k) != "f":
                continue
            old = nt.val[k]
            nt.val[k] = v
            if _same.moved(old, v):
                moved.add(k)
                self.say(rno, "in", k, v)
        for k in self.by(moved):
            for r in self.by(nt.rdr.get(k, ())):
                _ord.wake(self.pl, nt, r)
        self.spin(rno, moved)
        for t in _trip.due(self.pl, nt, "end", rno, None, moved):
            self.pop(rno, t)
        return _trip.sched(self.pl, nt, tuple(self.fired))

    def go(self):
        self.build()
        rno = 0
        for w in self.rounds:
            rno += 1
            if rno > TURNS:
                raise Stop("turns")
            nx = self.turn(rno, w)
            while nx:
                rno += 1
                if rno > TURNS:
                    raise Stop("turns")
                nx = self.turn(rno, nx)
        return tuple((n, self.net.val[n]) for n in sorted(self.net.ix, key=lambda m: m))
