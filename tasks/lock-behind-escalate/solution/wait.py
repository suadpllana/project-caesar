from lm import spec


class Req:
    __slots__ = ("seq", "txn", "tgt", "mode")

    def __init__(self, seq, txn, tgt, mode):
        self.seq = seq
        self.txn = txn
        self.tgt = tgt
        self.mode = mode


class Wait:
    __slots__ = ("seq", "queue", "of", "at", "rows")

    def __init__(self):
        self.seq = 0
        self.queue = []
        self.of = {}
        self.at = {}
        self.rows = {}

    def next(self):
        self.seq += 1
        return self.seq

    def add(self, req):
        self.queue.append(req)
        self.of[req.txn] = req
        self.at.setdefault((req.tgt, req.mode), []).append(req)
        if spec.is_row(req.tgt):
            self.rows.setdefault((spec.table_of(req.tgt), req.mode), []).append(req)

    def remove(self, req):
        self.queue.remove(req)
        del self.of[req.txn]
        self._drop(self.at, (req.tgt, req.mode), req)
        if spec.is_row(req.tgt):
            self._drop(self.rows, (spec.table_of(req.tgt), req.mode), req)

    @staticmethod
    def _drop(index, key, req):
        held = index[key]
        held.remove(req)
        if not held:
            del index[key]

    def clashing(self, tgt, mode):
        table = spec.table_of(tgt)
        keys = [(tgt, "x"), (table, "x")] if spec.is_row(tgt) else [(tgt, "x")]
        if mode == "x":
            keys.append((tgt, "s"))
            if spec.is_row(tgt):
                keys.append((table, "s"))
        for key in keys:
            yield from self.at.get(key, ())
        if not spec.is_row(tgt):
            yield from self.rows.get((tgt, "x"), ())
            if mode == "x":
                yield from self.rows.get((tgt, "s"), ())
