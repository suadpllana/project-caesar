from store import agg


class Route:
    def __init__(self, core, ms, spec, wm):
        self.core = core
        self.ms = ms
        self.spec = spec
        self.wm = wm

    def kinds_for(self, src):
        out = []
        for kind, srcs in self.spec.items():
            if src in srcs:
                out.append(kind)
        return sorted(out)

    def push(self, d, edits):
        by_g = {}
        for e in edits:
            by_g.setdefault(e.g, []).append(e)
        for g in sorted(by_g):
            for kind in self.kinds_for(d.src):
                self._one(d.src, g, kind, by_g[g])
        return sorted(by_g)

    def _one(self, src, g, kind, es):
        cell = self.core.cells.get((g, kind))
        if cell is None or self._absorbable(src, g, cell, kind, es):
            for e in es:
                self.core.apply(g, kind, e.v, e.w, e.rk)
            return
        self.core.rebuild(g, kind, self._needed(src, g, kind))

    def _needed(self, src, g, kind):
        rows = self.ms.group(src, g)
        best = sorted({r.v for r in rows}, key=lambda v: agg._rank(kind, v))[:agg.CAP]
        keep = set(best)
        return [r for r in rows if r.v in keep]
    def _absorbable(self, src, g, cell, kind, es):
        if kind in (agg.SUM, agg.CNT):
            return True
        neg = [e for e in es if e.w < 0]
        if not neg:
            return True
        empties = False
        held = dict(cell.acc.top)
        for e in neg:
            c = held.get(e.v)
            if c is None:
                continue
            held[e.v] = c + e.w
            if held[e.v] < 1:
                empties = True
        if not empties:
            return True
        live = {e.v for e in neg}
        for r in self.ms.group(src, g):
            live.add(r.v)
        return len(live) <= len(cell.acc.top)
