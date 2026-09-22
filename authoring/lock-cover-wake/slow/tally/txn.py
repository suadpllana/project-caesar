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
    best = t.seq
    hp = t.hp
    aside = []
    while hp:
        val, res = hp[0]
        if res not in t.held:
            heapq.heappop(hp)
            continue
        e = ents.get(res)
        if e is None or e.old != val:
            heapq.heappop(hp)
            continue
        if res == skip:
            aside.append(heapq.heappop(hp))
            continue
        break
    if hp and hp[0][0] < best:
        best = hp[0][0]
    for it in aside:
        heapq.heappush(hp, it)
    return best
