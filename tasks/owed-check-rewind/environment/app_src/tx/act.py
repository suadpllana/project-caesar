class Act:
    def __init__(self, cat, heap):
        self.cat = cat
        self.heap = heap

    def insert(self, tn, k, vals):
        if self.heap.has(tn, k):
            return ("key", tn, k)
        self.heap.put(tn, k, vals)
        return None

    def update(self, tn, k, sets):
        row = self.heap.get(tn, k)
        if row is not None:
            pos = self.cat.tables[tn].pos
            for col, v in sets:
                row[pos[col]] = v
        return None

    def delete(self, tn, k):
        if not self.heap.has(tn, k):
            return None
        self.heap.drop(tn, k)
        for fk in self.cat.fks_into(tn):
            kids = self.heap.holders(fk, k)
            if fk.action == "cascade":
                for c in kids:
                    self.delete(fk.table, c)
            elif fk.action == "setnull":
                i = self.cat.tables[fk.table].pos[fk.col]
                for c in kids:
                    self.heap.get(fk.table, c)[i] = None
        return None
