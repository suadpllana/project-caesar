class Txn:
    __slots__ = ("tid", "seq", "state", "held", "seen", "pend")

    def __init__(self, tid, seq):
        self.tid = tid
        self.seq = seq
        self.state = "run"
        self.held = {}
        self.seen = {}
        self.pend = None

    def take(self, res, m, tbl, row):
        self.held[res] = m

    def drop(self, res, tbl, row):
        self.held.pop(res, None)

    def bump(self, tbl):
        self.seen[tbl] = self.seen.get(tbl, 0) + 1

    def tally(self, tbl):
        return self.seen.get(tbl, 0)


def standing(t, skip, ents):
    return t.seq
