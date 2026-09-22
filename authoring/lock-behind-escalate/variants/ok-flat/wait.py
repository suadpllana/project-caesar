from lm import spec


class Req:
    __slots__ = ("seq", "txn", "tgt", "mode")

    def __init__(self, seq, txn, tgt, mode):
        self.seq = seq
        self.txn = txn
        self.tgt = tgt
        self.mode = mode

    def against(self, tgt, mode):
        """Does this request conflict with a lock on tgt in mode?"""
        if not (mode == "x" or self.mode == "x"):
            return False
        return self.tgt == tgt or spec.table_of(self.tgt) == tgt \
            or spec.table_of(tgt) == self.tgt


class Wait:
    __slots__ = ("counter", "pending", "per_table")

    def __init__(self):
        self.counter = 0
        self.pending = {}
        self.per_table = {}

    def stamp(self):
        self.counter += 1
        return self.counter

    def add(self, req):
        self.pending[req.txn] = req
        self.per_table.setdefault(spec.table_of(req.tgt), []).append(req)

    def remove(self, txn):
        req = self.pending.pop(txn)
        self.per_table[spec.table_of(req.tgt)].remove(req)

    def in_order(self):
        return sorted(self.pending.values(), key=lambda r: r.seq)

    def ahead_of(self, txn, tgt, mode, seq):
        """Transactions with an earlier conflicting request, in no particular order."""
        return {r.txn for r in self.per_table.get(spec.table_of(tgt), ())
                if r.txn != txn and r.seq < seq and r.against(tgt, mode)}
