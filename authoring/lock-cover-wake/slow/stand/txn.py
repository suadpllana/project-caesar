import heapq


class Txn:
    __slots__ = ("tid", "seq", "state", "held", "rows", "pend", "hp")

    def __init__(self, tid, seq):
        self.tid = tid
        self.seq = seq
        self.state = "run"
        self.held = {}
        self.rows = {}
        self.pend = None
        self.hp = []

    def take(self, res, m, tbl, row):
        self.held[res] = m
        if row >= 0:
            b = self.rows.get(tbl)
            if b is None:
                b = self.rows[tbl] = {}
            b[res] = m

    def drop(self, res, tbl, row):
        self.held.pop(res, None)
        if row >= 0:
            b = self.rows.get(tbl)
            if b is not None:
                b.pop(res, None)
                if not b:
                    del self.rows[tbl]

    def tally(self, tbl):
        b = self.rows.get(tbl)
        return 0 if b is None else len(b)

    def note(self, res, val):
        heapq.heappush(self.hp, (val, res))


def standing(t, skip, ents):
    """The standing worked out by walking every entry the holder holds."""
    best = t.seq
    for res in t.held:
        if res == skip:
            continue
        e = ents.get(res)
        if e is None or e.old is None:
            continue
        if e.old < best:
            best = e.old
    return best
