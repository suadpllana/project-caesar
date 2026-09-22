import bisect


class Txn:
    """Rows as a set per table with the modes read back out of `held`, and an exact
    sorted list of (begin, resource) for the shield rather than a lazily cleaned heap."""

    __slots__ = ("tid", "seq", "state", "held", "bag", "pend", "at", "keys")

    def __init__(self, tid, seq):
        self.tid = tid
        self.seq = seq
        self.state = "run"
        self.held = {}
        self.bag = {}
        self.pend = None
        self.at = {}
        self.keys = []

    def take(self, res, m, tbl, row):
        self.held[res] = m
        if row >= 0:
            s = self.bag.get(tbl)
            if s is None:
                s = self.bag[tbl] = set()
            s.add(res)

    def drop(self, res, tbl, row):
        self.held.pop(res, None)
        if row >= 0:
            s = self.bag.get(tbl)
            if s is not None:
                s.discard(res)
                if not s:
                    del self.bag[tbl]

    def rows_on(self, tbl):
        return [(res, self.held[res]) for res in sorted(self.bag.get(tbl, ()))]

    def tally(self, tbl):
        return len(self.bag.get(tbl, ()))

    def note(self, res, val):
        cur = self.at.get(res)
        if cur == val:
            return
        if cur is not None:
            self.keys.remove((cur, res))
            del self.at[res]
        if val is not None:
            self.at[res] = val
            bisect.insort(self.keys, (val, res))


def standing(t, skip, ents):
    best = t.seq
    for val, res in t.keys[:2]:
        if res == skip:
            continue
        if val < best:
            best = val
        break
    return best
