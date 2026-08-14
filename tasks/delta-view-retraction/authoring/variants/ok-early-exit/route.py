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
        seen = []
        for e in es:
            if e.w < 0 and e.v not in seen:
                seen.append(e.v)
        if not seen:
            return True
        for r in self.ms.group(src, g):
            if r.v not in seen:
                seen.append(r.v)
        if not len(seen) > len(cell.acc.top):
            return True
        left = dict(cell.acc.top)
        for e in es:
            if e.w >= 0:
                continue
            if e.v in left:
                left[e.v] = left[e.v] + e.w
                if left[e.v] < 1:
                    return False
        return True
