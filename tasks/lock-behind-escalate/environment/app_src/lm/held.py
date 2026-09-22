from lm import spec


class Held:
    __slots__ = ("rec",)

    def __init__(self):
        self.rec = {}

    def open(self, txn):
        self.rec[txn] = {}

    def mode(self, txn, tgt):
        return self.rec[txn].get(tgt)

    def count(self, txn):
        return len(self.rec[txn])

    def put(self, txn, tgt, mode):
        rs = self.rec[txn]
        if rs.get(tgt) != "x":
            rs[tgt] = mode

    def cut(self, txn, tgt):
        return self.rec[txn].pop(tgt, None) is not None

    def cut_all(self, txn):
        n = len(self.rec[txn])
        self.rec[txn] = {}
        return n

    def rows(self, txn, table):
        return [(t, m) for t, m in self.rec[txn].items()
                if spec.is_row(t) and spec.table_of(t) == table]

    def holders(self, txn):
        for u, rs in self.rec.items():
            if u != txn:
                for t, m in rs.items():
                    yield u, t, m
