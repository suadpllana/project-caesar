from lm import spec


class Held:
    __slots__ = ("rec", "on", "tab")

    def __init__(self):
        self.rec = {}
        self.on = {}
        self.tab = {}

    def open(self, txn):
        self.rec[txn] = {}

    def mode(self, txn, tgt):
        return self.rec[txn].get(tgt)

    def count(self, txn):
        return len(self.rec[txn])

    def put(self, txn, tgt, mode):
        rs = self.rec[txn]
        cur = rs.get(tgt)
        if cur is not None and (cur == "x" or mode == "s"):
            return
        rs[tgt] = mode
        self.on.setdefault(tgt, {})[txn] = mode
        if spec.is_row(tgt):
            tally = self.tab.setdefault(spec.table_of(tgt), {}).setdefault(txn, [0, 0])
            if cur is None:
                tally[0 if mode == "s" else 1] += 1
            else:
                tally[0] -= 1
                tally[1] += 1

    def cut(self, txn, tgt):
        rs = self.rec[txn]
        mode = rs.pop(tgt, None)
        if mode is None:
            return False
        del self.on[tgt][txn]
        if not self.on[tgt]:
            del self.on[tgt]
        if spec.is_row(tgt):
            table = spec.table_of(tgt)
            tally = self.tab[table][txn]
            tally[0 if mode == "s" else 1] -= 1
            if tally == [0, 0]:
                del self.tab[table][txn]
                if not self.tab[table]:
                    del self.tab[table]
        return True

    def cut_all(self, txn):
        n = 0
        for tgt in list(self.rec[txn]):
            self.cut(txn, tgt)
            n += 1
        return n

    def rows(self, txn, table):
        return [(t, m) for t, m in self.rec[txn].items()
                if spec.is_row(t) and spec.table_of(t) == table]

    def clashers(self, txn, tgt, mode):
        table = spec.table_of(tgt)
        for u, m in self.on.get(table, {}).items():
            if u != txn and (mode == "x" or m == "x"):
                yield u
        if spec.is_row(tgt):
            for u, m in self.on.get(tgt, {}).items():
                if u != txn and (mode == "x" or m == "x"):
                    yield u
        else:
            for u, (ns, nx) in self.tab.get(table, {}).items():
                if u != txn and (nx or (ns and mode == "x")):
                    yield u

    def covered(self, txn, tgt, mode):
        rs = self.rec[txn]
        for t in (tgt, spec.table_of(tgt)):
            m = rs.get(t)
            if m is not None and (m == "x" or mode == "s"):
                return True
        return False

    def subsume(self, txn, table, mode):
        for t, m in self.rows(txn, table):
            if mode == "x" or m == "s":
                self.cut(txn, t)
