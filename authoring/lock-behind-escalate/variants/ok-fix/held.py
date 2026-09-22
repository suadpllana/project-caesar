from lm import spec


class Held:
    __slots__ = ("by", "at", "rows")

    def __init__(self):
        self.by = {}
        self.at = {}
        self.rows = {}

    def open(self, txn):
        self.by[txn] = {}

    def mode(self, txn, tgt):
        return self.by[txn].get(tgt)

    def count(self, txn):
        return len(self.by[txn])

    def put(self, txn, tgt, mode):
        have = self.by[txn].get(tgt)
        if have == "x" or (have == "s" and mode == "s"):
            return
        self.by[txn][tgt] = mode
        self.at.setdefault(tgt, {})[txn] = mode
        if spec.is_row(tgt):
            self.rows.setdefault(spec.table_of(tgt), {}).setdefault(txn, {})[tgt] = mode

    def cut(self, txn, tgt):
        if tgt not in self.by[txn]:
            return False
        del self.by[txn][tgt]
        del self.at[tgt][txn]
        if spec.is_row(tgt):
            table = spec.table_of(tgt)
            del self.rows[table][txn][tgt]
            if not self.rows[table][txn]:
                del self.rows[table][txn]
        return True

    def cut_all(self, txn):
        n = 0
        for tgt in list(self.by[txn]):
            self.cut(txn, tgt)
            n += 1
        return n

    def row_modes(self, txn, table):
        return list(self.rows.get(table, {}).get(txn, {}).values())

    def blockers(self, txn, tgt, mode):
        """Other transactions whose records conflict with a lock on tgt in mode."""
        found = set()
        table = spec.table_of(tgt)
        pool = list(self.at.get(tgt, {}).items())
        if spec.is_row(tgt):
            pool += self.at.get(table, {}).items()
        for u, m in pool:
            if u != txn and (m == "x" or mode == "x"):
                found.add(u)
        if not spec.is_row(tgt):
            for u, mine in self.rows.get(table, {}).items():
                if u != txn and (mode == "x" or "x" in mine.values()):
                    found.add(u)
        return found

    def covers(self, txn, tgt, mode):
        for t in (tgt, spec.table_of(tgt)):
            m = self.by[txn].get(t)
            if m == "x" or (m == "s" and mode == "s"):
                return True
        return False

    def fold(self, txn, table, mode):
        for t, m in list(self.rows.get(table, {}).get(txn, {}).items()):
            if mode == "x" or m == "s":
                self.cut(txn, t)
