"""An alternative correct plan: the stop rule stated as a depth rather than as a flag.

The reference decides when to stop pulling with a flag it clears whenever a deeper chain
start appears. This keeps the index of the deepest start instead and asks, each time a
record arrives, whether anything at or below that index terminates a chain. Same records
pulled, same records written, same point reads - which is the point of keeping it.
"""

from seg import rec


class Plan:
    def __init__(self, core):
        self.core = core

    def key(self, cur, pts):
        rs = []
        pend = sorted(pts)
        deep = -1
        while True:
            r = cur.next()
            if r is None:
                break
            rs.append(r)
            while pend and pend[-1] >= r.s:
                pend.pop()
                deep = len(rs) - 1
            if not pend and deep >= 0 and self.closed(rs, deep):
                break
        if not rs:
            return
        starts = []
        for a in sorted(pts):
            i = 0
            while i < len(rs) and rs[i].s > a:
                i += 1
            if i < len(rs) and i not in starts:
                starts.append(i)
        if not starts:
            return
        outs = [(rs[i].s,) + self.chain(rs, i) for i in starts]
        self.place(cur.k, outs)

    def closed(self, rs, start):
        for x in rs[start:]:
            if x.t != rec.ADD:
                return True
        return False

    def chain(self, rs, i):
        acc = 0
        n = 0
        for x in rs[i:]:
            if x.t == rec.ADD:
                acc += x.v
                n += 1
            elif x.t == rec.PUT:
                return ("v", acc + x.v)
            else:
                return ("v", acc) if n else ("z", 0)
        return ("o", acc)

    def place(self, k, outs):
        known = not (outs[0][1] == "o" and outs[0][2])
        base = self.core.probe(k) if known else None
        held = (("v", base) if base is not None else ("z", 0)) if known else None
        run = 0
        for s, kind, val in outs:
            if kind == "v":
                res = ("v", val)
            elif kind == "z":
                res = ("z", 0)
            elif not known:
                res = ("o", val)
            else:
                res = ("v", val if base is None else val + base)
            if res == held:
                if kind == "o":
                    run = val
                continue
            if kind == "v":
                self.core.emit(k, s, rec.PUT, val)
            elif kind == "z":
                self.core.emit(k, s, rec.DEL, 0)
            else:
                self.core.emit(k, s, rec.ADD, val - run)
                run = val
            held = res
