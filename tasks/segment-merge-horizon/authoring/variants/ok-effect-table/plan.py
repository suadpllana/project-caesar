"""An alternative correct plan: resolve every read point to an effect first, decide later.

This one builds the whole table of what each read point has to answer before it thinks about
records at all, then walks the table from the bottom emitting wherever the answer changes.
It asks the rest of the store up front for every key whose lowest answer could be affected
by it, which is the same set the reference asks about, and it closes an open answer with an
absolute record when it has a base for one. Same three counters as the reference on every
scenario.
"""

from seg import rec

MISS = ("miss",)


class Plan:
    def __init__(self, core):
        self.core = core

    def key(self, cur, pts):
        pending = sorted(pts)
        rows = []
        depth = None
        while pending or depth is None or not self.done(rows, depth):
            r = cur.next()
            if r is None:
                break
            rows.append(r)
            take = [a for a in pending if r.s <= a]
            if take:
                depth = len(rows) - 1
                pending = [a for a in pending if a not in take]
        if not rows:
            return
        table = []
        prev = None
        for a in sorted(pts):
            i = self.start(rows, a)
            if i is None or i == prev:
                continue
            prev = i
            table.append((rows[i].s, self.effect(rows, i)))
        if table:
            self.lay(cur.k, table)

    def done(self, rows, depth):
        if depth is None or depth >= len(rows):
            return False
        for x in rows[depth:]:
            if x.t != rec.ADD:
                return True
        return False

    def start(self, rows, a):
        for i, x in enumerate(rows):
            if x.s <= a:
                return i
        return None

    def effect(self, rows, i):
        acc = 0
        n = 0
        for x in rows[i:]:
            if x.t == rec.ADD:
                acc += x.v
                n += 1
            elif x.t == rec.PUT:
                return ("set", acc + x.v)
            elif n:
                return ("set", acc)
            else:
                return ("gone", 0)
        return ("open", acc)

    def lay(self, k, table):
        ask = table[0][1][0] != "open" or table[0][1][1] == 0
        base = self.core.probe(k) if ask else None
        under = MISS
        if ask:
            under = ("set", base) if base is not None else ("gone", 0)
        carried = 0
        for s, eff in table:
            kind, val = eff
            if kind == "open" and ask:
                shown = ("set", val if base is None else val + base)
            else:
                shown = eff
            if shown == under:
                if kind == "open":
                    carried = val
                continue
            if kind == "set":
                self.core.emit(k, s, rec.PUT, val)
            elif kind == "gone":
                self.core.emit(k, s, rec.DEL, 0)
            elif ask:
                self.core.emit(k, s, rec.PUT, shown[1])
                carried = val
            else:
                self.core.emit(k, s, rec.ADD, val - carried)
                carried = val
            under = shown
