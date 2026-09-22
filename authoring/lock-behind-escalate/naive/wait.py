from lm import spec


class Req:
    __slots__ = ("seq", "txn", "tgt", "mode")

    def __init__(self, seq, txn, tgt, mode):
        self.seq = seq
        self.txn = txn
        self.tgt = tgt
        self.mode = mode


class Wait:
    __slots__ = ("seq", "queue", "of", "tab")

    def __init__(self):
        self.seq = 0
        self.queue = []
        self.of = {}
        self.tab = {}

    def next(self):
        self.seq += 1
        return self.seq

    def add(self, req):
        self.queue.append(req)
        self.of[req.txn] = req
        self.tab.setdefault(spec.table_of(req.tgt), []).append(req)

    def remove(self, req):
        self.queue.remove(req)
        del self.of[req.txn]
        table = spec.table_of(req.tgt)
        self.tab[table].remove(req)
        if not self.tab[table]:
            del self.tab[table]

    def on(self, table):
        return self.tab.get(table, ())
