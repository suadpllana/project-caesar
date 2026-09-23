"""ok-region: correct variant with a heap per region, belief nested by node, memoised walks.

Written to the contract without reference to the solution. Must score 1.
"""
from . import say, unit
from .know import Know
from .line import Line
from .look import Look
from .watch import Watch, value


class Reader:
    def __init__(self, pg):
        self.pg = pg
        self.look = Look(pg)
        self.know = Know()
        self.line = Line()
        self.watch = Watch(pg, self.look, self.know, self.line)
        self.playing = None

    def load(self):
        pg, look = self.pg, self.look
        for x in pg.walk(0):
            if pg.is_text(x):
                shown, reg = look.where(x)
                if shown and reg is not None:
                    self.know.set_bel(x, reg, (pg.text(x), pg.up(x)))

    def _regions(self, loud):
        return [r for r in self.line.heaps if self.pg.attr(r, "aria-live") == loud]

    def _next(self):
        k = self.line.best(self._regions("assertive"))
        if k is None:
            k = self.line.best(self._regions("polite"))
        return k

    def step(self, t, recs):
        pg, look, know, line, watch = self.pg, self.look, self.know, self.line, self.watch
        look.forget()
        out = []
        if self.playing is not None and self.playing[1] == t:
            know.teach()
            self.playing = None
        watch.observe(t, recs)
        if self.playing is not None and self.playing[0] == "polite" and \
                line.best(self._regions("assertive")) is not None:
            out.append(say.cut(t))
            self.playing = None
            for k, (_v, age) in know.drop_carry().items():
                watch.judge(k, t, age=age)
        while self.playing is None:
            k0 = self._next()
            if k0 is None:
                break
            r0, n0 = k0
            c0 = value(pg, look, n0, r0)
            u = unit.unit(pg, look, know, k0, c0)
            if u is None:
                group = [k0]
                words = c0[0] if c0 is not None else "removed " + know.expect(n0, r0)[0]
            else:
                words = unit.spoken(pg, u)
                group = []
                for k in list(line.by_region.get(r0, ())):
                    if k in line.held:
                        continue
                    if unit.unit(pg, look, know, k, value(pg, look, k[1], r0)) == u:
                        group.append(k)
            items = {k: (value(pg, look, k[1], k[0]), line.age[k]) for k in group}
            for k in group:
                line.remove(k)
            if not words:
                for (r, n), (v, _a) in items.items():
                    know.set_bel(n, r, v)
                continue
            loud = pg.attr(r0, "aria-live")
            know.carry(items)
            self.playing = (loud, t + len(words.split(" ")))
            out.append(say.start(t, loud, words))
        return out
