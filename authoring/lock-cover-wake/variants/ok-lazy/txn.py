import heapq


class Txn:
    """Rows per table, and the shield as a heap validated against the value last noted."""

    __slots__ = ("tid", "seq", "state", "held", "rows", "pend", "at", "hp")

    def __init__(self, tid, seq):
        self.tid = tid
        self.seq = seq
        self.state = "run"
        self.held = {}
        self.rows = {}
        self.pend = None
        self.at = {}
        self.hp = []

    def take(self, res, m, tbl, row):
        self.held[res] = m
        if row >= 0:
            self.rows.setdefault(tbl, {})[res] = m

    def drop(self, res, tbl, row):
        self.held.pop(res, None)
        if row >= 0:
            bag = self.rows.get(tbl)
            if bag is not None:
                bag.pop(res, None)
                if not bag:
                    del self.rows[tbl]
        self.at.pop(res, None)

    def tally(self, tbl):
        bag = self.rows.get(tbl)
        return 0 if bag is None else len(bag)

    def note(self, res, val):
        if val is None:
            self.at.pop(res, None)
            return
        if self.at.get(res) == val:
            return
        self.at[res] = val
        heapq.heappush(self.hp, (val, res))


def standing(t, skip, ents):
    best = t.seq
    keep = []
    while t.hp:
        val, res = t.hp[0]
        if t.at.get(res) != val:
            heapq.heappop(t.hp)
            continue
        if res == skip:
            keep.append(heapq.heappop(t.hp))
            continue
        if val < best:
            best = val
        break
    for it in keep:
        heapq.heappush(t.hp, it)
    return best
