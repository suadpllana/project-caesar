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
        self.core.rebuild(g, kind, self.ms.group(src, g))
    def _absorbable(self, src, g, cell, kind, es):
        if kind in (agg.SUM, agg.CNT):
            return True
        neg = [e for e in es if e.w < 0]
        if not neg:
            return True
        live = {e.v for e in neg}
        for r in self.ms.group(src, g):
            live.add(r.v)
        if len(live) <= len(cell.acc.top):
            return True
        held = dict(cell.acc.top)
        for e in neg:
            c = held.get(e.v)
            if c is not None:
                if c + e.w < 1:
                    return False
                held[e.v] = c + e.w
        return True
