"""Observation: which differences exist at the end of a tick, and what happens to each.

A difference is measured per (region, text node) between the current value - the node's text and
parent when it is exposed in that region - and what the reader will believe once the playing
utterance finishes, by presence and text only. A difference the reader cannot voice (its region
is off or not exposed) or that its region does not find relevant is absorbed on the spot; every
other one is in the waiting line, keeping the age of the tick that first observed it.

The rule is stated for every key on every tick. Doing that literally is correct, and it is exactly
what the wide pages are there to rule out, so this only looks at keys something could have changed:

- a text record changes one node;
- adding, moving or dropping a node, or hiding or showing an element, changes the exposure,
  region or parent of every text node beneath it, changes whether every removal anchored beneath
  it is still placed there, and changes whether every region element beneath it is exposed;
- an aria-live or aria-relevant change on a region element reclassifies every difference in it;
- an aria-busy change can only hold or release differences in the region the element is in.

Nothing else on the page can change a key's value, whether it may be voiced, or what holds it.
"""
from . import look, unit


def differs(c, e):
    if (c is None) != (e is None):
        return True
    return c is not None and c[0] != e[0]


def kind(c, e):
    if e is None:
        return "additions"
    if c is None:
        return "removals"
    return "text"


class Watch:
    def __init__(self, pg, know, line):
        self.pg = pg
        self.know = know
        self.line = line

    def now(self, n):
        """(region, (text, parent)) for text node n exposed in a region, else (None, None)."""
        shown, r = look.place(self.pg, n)
        if not shown or r is None:
            return None, None
        return r, (self.pg.text(n), self.pg.up(n))

    def survey(self):
        out = {}
        pg = self.pg
        todo = [(0, None)]
        while todo:
            x, r = todo.pop()
            if pg.is_text(x):
                if r is not None:
                    out[(r, x)] = (pg.text(x), pg.up(x))
                continue
            if look.hides(pg, x):
                continue
            if pg.attr(x, "aria-live") is not None:
                r = x
            for y in pg.kids(x):
                todo.append((y, r))
        return out

    def settle(self, k, t, age=None, where=None):
        pg, know, line = self.pg, self.know, self.line
        r, n = k
        rr, cur = self.now(n) if where is None else where
        c = cur if rr == r else None
        e = know.expect(k)
        if not differs(c, e):
            line.drop(k)
            return
        if not look.voicing(pg, r) or kind(c, e) not in look.relevant(pg, r):
            know.absorb(k, c)
            line.drop(k)
            return
        if age is None:
            age = line.age.get(k, t)
        line.put(k, age, look.loudness(pg, r), unit.held(pg, know, k, c),
                 e[1] if c is None else None)

    def rehold(self, k):
        if k not in self.line.age:
            return
        r, n = k
        rr, cur = self.now(n)
        c = cur if rr == r else None
        self.line.hold(k, unit.held(self.pg, self.know, k, c))

    def _sweep(self, top, nodes, anchors, regs):
        pg = self.pg
        for x in pg.walk(top):
            if pg.is_text(x):
                nodes.add(x)
            else:
                anchors.add(x)
                if pg.attr(x, "aria-live") is not None:
                    regs.add(x)

    def scan(self, recs, t):
        pg = self.pg
        nodes, anchors, regs, busy = set(), set(), set(), set()
        for rec in recs:
            head = rec[0]
            if head == "text":
                nodes.add(rec[1])
            elif head in ("add", "move", "drop"):
                self._sweep(rec[1], nodes, anchors, regs)
            else:
                e, name = rec[1], rec[2]
                if name in ("hidden", "aria-hidden"):
                    self._sweep(e, nodes, anchors, regs)
                elif name in ("aria-live", "aria-relevant"):
                    if pg.attr(e, "aria-live") is not None:
                        regs.add(e)
                elif name == "aria-busy":
                    q = look.region(pg, e)
                    if q is not None:
                        busy.add(q)
        for n in nodes:
            where = self.now(n)
            ks = {(q, n) for q in self.know.regions_of(n)}
            ks.update((q, n) for q in self.line.regions_of(n))
            if where[0] is not None:
                ks.add((where[0], n))
            for k in ks:
                self.settle(k, t, where=where)
        for r in regs:
            for k in self.line.of_region(r):
                self.settle(k, t)
        for a in anchors:
            for k in self.line.anchored(a):
                self.rehold(k)
        for q in busy:
            for k in self.line.of_region(q):
                self.rehold(k)
