from ingest import delta, wm
from store import agg, rows
from view import core, land, route, seal


class Drv:
    def __init__(self, cfg):
        self.cfg = cfg
        self.spec = cfg["view"]
        self.ms = rows.Mset()
        self.wm = wm.Wm(cfg["lag"])
        self.core = core.Core(self.spec)
        self.seal = seal.Sealer(self.wm)
        self.route = route.Route(self.core, self.ms, self.spec, self.wm)
        self.trace = []
        self.seq = 0

    def feed(self, rec):
        self.seq += 1
        d = delta.parse(rec, self.seq)
        self.core.tick(self.seq)
        before = self.wm.cur
        self.wm.observe(d.ts)
        after = self.wm.cur
        if d.ts <= before:
            self.trace.append(["late", d.seq, d.src, d.k])
            self.seal.revised += 1
        self.route.push(d, land.land(self.ms, d))
        if after > before:
            self._close(after)
        return d

    def _close(self, hi):
        self.trace.append(["wm", self.seq, hi])
        for kind in sorted(set(self.spec)):
            for g in self.core.groups():
                if (g, kind) not in self.core.cells:
                    continue
                val = self.core.emit(g, kind, self.seq)
                self.seal.mark(g, kind, hi)
                self.trace.append(["emit", self.seq, g, kind, val])

    def run(self, recs):
        for rec in recs:
            self.feed(rec)
        return self.report()

    def report(self):
        return {
            "view": self.core.report(),
            "folds": self.core.folds,
            "scans": self.core.scans,
            "emits": self.core.emits,
            "revised": self.seal.revised,
            "trace": [list(t) for t in self.trace],
            "log": [list(x) for x in self.core.log],
            "jrn": [list(x) for x in self.core.jrn],
            "deep": [list(x) for x in agg.JRN],
        }
