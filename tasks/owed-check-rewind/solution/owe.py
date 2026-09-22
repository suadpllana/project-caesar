from tx import chk


class Owe:
    """The ledger of owed checks: (constraint, table, key) -> the number it was recorded under.
    Order is (declaration index, number), computed from the entry and not from a container, so
    an entry a rollback puts back is in its old place. Changes are journalled with old numbers."""

    def __init__(self, cat, heap, log):
        self.cat = cat
        self.heap = heap
        self.log = log
        self.num = {}
        self.n = 0

    def clear(self):
        self.num = {}

    def place(self, entry):
        return (self.cat.con(entry[0]).idx, self.num[entry])

    def listed(self, names=None):
        out = [e for e in self.num if names is None or e[0] in names]
        out.sort(key=self.place)
        return out

    def add(self, entry):
        self.n += 1
        self.log.note(("owe", entry, None))
        self.num[entry] = self.n

    def remove(self, entry):
        self.log.note(("owe", entry, self.num.pop(entry)))

    def restore(self, entry, n):
        if n is None:
            self.num.pop(entry, None)
        else:
            self.num[entry] = n

    def judge(self, cons, order, seen):
        """At the end of a statement: every deferred constraint looks at the rows and keys the
        statement touched, and only at those. Returns (removed, added), each in ledger order."""
        removed, added = [], []
        for con in cons:
            for tn, k in order:
                how = seen[(tn, k)]
                if tn == con.table:
                    bad = chk.broken(self.cat, self.heap, con, tn, k)
                elif con.kind == "fk" and tn == con.parent and ("d" in how or "i" in how):
                    bad = chk.stranded(self.heap, con, k)
                else:
                    continue
                entry = (con.name, tn, k)
                if bad and entry not in self.num:
                    self.add(entry)
                    added.append(entry)
                elif not bad and entry in self.num:
                    removed.append((self.place(entry), entry))
                    self.remove(entry)
        removed.sort()
        added.sort(key=self.place)
        return [e for _, e in removed], added

    def first_live(self, names):
        """The first entry of these constraints, in ledger order, that is still a violation,
        and the entries a successful check point would clear."""
        mine = self.listed(names)
        for entry in mine:
            if chk.still(self.cat, self.heap, entry):
                return entry, mine
        return None, mine
