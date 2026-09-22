"""ok-region: observation from the tick's records, with precise re-holds by subtree."""
from . import unit


def value(pg, look, n, r):
    shown, reg = look.where(n)
    if shown and reg == r:
        return (pg.text(n), pg.up(n))
    return None


class Watch:
    def __init__(self, pg, look, know, line):
        self.pg, self.look, self.know, self.line = pg, look, know, line

    def judge(self, k, t, age=None):
        pg, look, know, line = self.pg, self.look, self.know, self.line
        r, n = k
        c = value(pg, look, n, r)
        e = know.expect(n, r)
        same = (c is None and e is None) or (c is not None and e is not None and c[0] == e[0])
        if same:
            line.remove(k)
            return
        kind = "additions" if e is None else ("removals" if c is None else "text")
        if not look.speaks(r) or kind not in look.kinds(r):
            know.release(n, r)
            know.set_bel(n, r, c)
            line.remove(k)
            return
        if age is None:
            age = line.age.get(k, t)
        line.add(k, age, unit.held(pg, look, know, k, c), e[1] if c is None else None)

    def rejudge_hold(self, k):
        if not self.line.has(k):
            return
        r, n = k
        c = value(self.pg, self.look, n, r)
        self.line.set_held(k, unit.held(self.pg, self.look, self.know, k, c))

    def keys_for(self, n):
        shown, reg = self.look.where(n)
        rs = set(self.know.regions(n)) | set(self.line.by_node.get(n, ()))
        if shown and reg is not None:
            rs.add(reg)
        return [(r, n) for r in rs]

    def observe(self, t, recs):
        pg, look, line = self.pg, self.look, self.line
        texts, anchors, regions, busy_tops = set(), set(), set(), set()

        def sweep(top):
            for x in pg.walk(top):
                if pg.is_text(x):
                    texts.add(x)
                else:
                    anchors.add(x)
                    if pg.attr(x, "aria-live") is not None:
                        regions.add(x)

        for rec in recs:
            h = rec[0]
            if h == "text":
                texts.add(rec[1])
            elif h in ("add", "move", "drop"):
                sweep(rec[1])
            else:
                e, name = rec[1], rec[2]
                if name in ("hidden", "aria-hidden"):
                    sweep(e)
                elif name in ("aria-live", "aria-relevant") and pg.attr(e, "aria-live") is not None:
                    regions.add(e)
                elif name == "aria-busy":
                    busy_tops.add(e)
        for n in texts:
            for k in self.keys_for(n):
                self.judge(k, t)
        for r in regions:
            for k in list(line.by_region.get(r, ())):
                self.judge(k, t)
        for a in anchors:
            for k in list(line.anchors.get(a, ())):
                self.rejudge_hold(k)
        for e in busy_tops:
            if pg.attr(e, "aria-live") is not None:
                for k in list(line.by_region.get(e, ())):
                    self.rejudge_hold(k)
                continue
            for x in pg.walk(e):
                if pg.is_text(x):
                    for r in list(line.by_node.get(x, ())):
                        self.rejudge_hold((r, x))
                else:
                    for k in list(line.anchors.get(x, ())):
                        self.rejudge_hold(k)
