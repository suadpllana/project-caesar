from lm import spec


class Wait:
    __slots__ = ("counter", "req", "order", "keyed")

    def __init__(self):
        self.counter = 0
        self.req = {}
        self.order = []
        self.keyed = {}

    def stamp(self):
        self.counter += 1
        return self.counter

    def park(self, seq, txn, tgt, mode):
        self.req[txn] = (seq, tgt, mode)
        self.order.append(txn)
        self.keyed.setdefault((tgt, mode), set()).add(txn)
        if spec.is_row(tgt):
            self.keyed.setdefault((spec.table_of(tgt), "*" + mode), set()).add(txn)

    def unpark(self, txn):
        seq, tgt, mode = self.req.pop(txn)
        self.order.remove(txn)
        self.keyed[(tgt, mode)].discard(txn)
        if spec.is_row(tgt):
            self.keyed[(spec.table_of(tgt), "*" + mode)].discard(txn)

    def waiting(self):
        return list(self.order)

    def rivals(self, txn, tgt, mode, before):
        """Transactions with an earlier waiting request that conflicts with (tgt, mode)."""
        table = spec.table_of(tgt)
        keys = [(tgt, "x")]
        if mode == "x":
            keys.append((tgt, "s"))
        if spec.is_row(tgt):
            keys.append((table, "x"))
            if mode == "x":
                keys.append((table, "s"))
        else:
            keys.append((tgt, "*x"))
            if mode == "x":
                keys.append((tgt, "*s"))
        out = set()
        for key in keys:
            for u in self.keyed.get(key, ()):
                if u != txn and self.req[u][0] < before:
                    out.add(u)
        return out
