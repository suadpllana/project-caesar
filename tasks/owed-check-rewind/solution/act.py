from tx import chk


class Raise(Exception):
    """A constraint raised inside a statement: (constraint name, table, key)."""


class Act:
    """One statement's writes: row checks, the referential walk, and first-touch order."""

    def __init__(self, cat, heap, mode):
        self.cat = cat
        self.heap = heap
        self.mode = mode
        self.start()

    def start(self):
        self.seen = {}
        self.order = []

    def touch(self, tn, k, how):
        key = (tn, k)
        if key not in self.seen:
            self.seen[key] = ""
            self.order.append(key)
        self.seen[key] += how

    def write(self, tn, k, vals):
        """Insert, update and setnull all come here: the row is checked as written."""
        self.heap.put(tn, k, vals)
        self.touch(tn, k, "w")
        for con in self.cat.checks_on(tn):
            if self.mode[con.name] == "i" and chk.broken(self.cat, self.heap, con, tn, k):
                raise Raise(con.name, tn, k)

    def insert(self, tn, k, vals):
        if self.heap.has(tn, k):
            raise Raise("key", tn, k)
        self.touch(tn, k, "i")
        self.write(tn, k, tuple(vals))

    def update(self, tn, k, sets):
        row = self.heap.get(tn, k)
        if row is None:
            return
        row = list(row)
        pos = self.cat.tables[tn].pos
        for col, v in sets:
            row[pos[col]] = v
        self.write(tn, k, tuple(row))

    def delete(self, tn, k):
        if self.heap.has(tn, k):
            self.remove(tn, k)

    def remove(self, tn, k):
        """Remove a row, then walk the keys that refer to its table in declaration order,
        each over the rows holding the key at the moment that key is reached, depth-first."""
        self.heap.put(tn, k, None)
        self.touch(tn, k, "d")
        for fk in self.cat.fks_into(tn):
            holders = self.heap.holders(fk, k)
            if not holders or fk.action == "noaction":
                continue
            if fk.action == "restrict":
                raise Raise(fk.name, tn, k)
            i = self.cat.tables[fk.table].pos[fk.col]
            for c in holders:
                row = self.heap.get(fk.table, c)
                if row is None:
                    continue
                if fk.action == "cascade":
                    self.remove(fk.table, c)
                else:
                    self.write(fk.table, c, row[:i] + (None,) + row[i + 1:])

    def finish(self):
        """End of statement: immediate foreign keys, in declaration order, over the rows the
        statement wrote and the parent keys it deleted, in the order they were first touched."""
        for fk in self.cat.cons:
            if fk.kind != "fk" or self.mode[fk.name] != "i":
                continue
            for tn, k in self.order:
                how = self.seen[(tn, k)]
                if tn == fk.table and "w" in how and chk.broken(self.cat, self.heap, fk, tn, k):
                    raise Raise(fk.name, tn, k)
                if tn == fk.parent and "d" in how and chk.stranded(self.heap, fk, k):
                    raise Raise(fk.name, tn, k)
