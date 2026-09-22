from lm import spec


class Table:
    __slots__ = ("name", "whole", "rows")

    def __init__(self, name):
        self.name = name
        self.whole = {}
        self.rows = {}

    def conflicts(self, txn, tgt, mode):
        out = []
        for u, m in self.whole.items():
            if u != txn and (m == "x" or mode == "x"):
                out.append(u)
        if tgt == self.name:
            for held in self.rows.values():
                for u, m in held.items():
                    if u != txn and (m == "x" or mode == "x"):
                        out.append(u)
        else:
            for u, m in self.rows.get(tgt, {}).items():
                if u != txn and (m == "x" or mode == "x"):
                    out.append(u)
        return out


class Held:
    __slots__ = ("tables", "mine")

    def __init__(self):
        self.tables = {}
        self.mine = {}

    def table(self, name):
        if name not in self.tables:
            self.tables[name] = Table(name)
        return self.tables[name]

    def open(self, txn):
        self.mine[txn] = set()

    def mode(self, txn, tgt):
        tab = self.tables.get(spec.table_of(tgt))
        if tab is None:
            return None
        if tgt == tab.name:
            return tab.whole.get(txn)
        return tab.rows.get(tgt, {}).get(txn)

    def count(self, txn):
        return len(self.mine[txn])

    def put(self, txn, tgt, mode):
        have = self.mode(txn, tgt)
        if have == "x" or have == mode:
            return
        tab = self.table(spec.table_of(tgt))
        if tgt == tab.name:
            tab.whole[txn] = mode
        else:
            tab.rows.setdefault(tgt, {})[txn] = mode
        self.mine[txn].add(tgt)

    def cut(self, txn, tgt):
        if tgt not in self.mine[txn]:
            return False
        tab = self.tables[spec.table_of(tgt)]
        if tgt == tab.name:
            del tab.whole[txn]
        else:
            del tab.rows[tgt][txn]
            if not tab.rows[tgt]:
                del tab.rows[tgt]
        self.mine[txn].discard(tgt)
        return True

    def cut_all(self, txn):
        n = 0
        for tgt in list(self.mine[txn]):
            self.cut(txn, tgt)
            n += 1
        return n

    def row_modes(self, txn, table):
        tab = self.tables.get(table)
        if tab is None:
            return []
        return [held[txn] for held in tab.rows.values() if txn in held]

    def against(self, txn, tgt, mode):
        tab = self.tables.get(spec.table_of(tgt))
        return [] if tab is None else tab.conflicts(txn, tgt, mode)

    def covered(self, txn, tgt, mode):
        for t in (tgt, spec.table_of(tgt)):
            have = self.mode(txn, t)
            if have == "x" or (have == "s" and mode == "s"):
                return True
        return False

    def absorb(self, txn, table, mode):
        tab = self.tables.get(table)
        if tab is None:
            return
        for row, held in list(tab.rows.items()):
            m = held.get(txn)
            if m is not None and (mode == "x" or m == "s"):
                self.cut(txn, row)
