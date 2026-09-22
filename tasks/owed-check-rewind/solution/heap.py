class Heap:
    """Rows by table and key as tuples, and for every foreign key the child keys holding each
    value. raw() keeps both in step, so undoing a row through it restores the index too."""

    def __init__(self, cat, rows):
        self.cat = cat
        self.log = None
        self.t = {n: {} for n in cat.tables}
        self.held = {f.name: {} for f in cat.cons if f.kind == "fk"}
        self.refs = {n: [(f.name, cat.tables[n].pos[f.col]) for f in cat.fks_from(n)]
                     for n in cat.tables}
        for tn, k, vals in rows:
            self.raw(tn, k, tuple(vals))

    def get(self, tn, k):
        return self.t[tn].get(k)

    def has(self, tn, k):
        return k in self.t[tn]

    def raw(self, tn, k, vals):
        """Set or remove one row without journalling it; returns what was there."""
        old = self.t[tn].get(k)
        for name, i in self.refs[tn]:
            if old is not None and old[i] is not None:
                self.held[name][old[i]].discard(k)
            if vals is not None and vals[i] is not None:
                self.held[name].setdefault(vals[i], set()).add(k)
        if vals is None:
            self.t[tn].pop(k, None)
        else:
            self.t[tn][k] = vals
        return old

    def put(self, tn, k, vals):
        self.log.note(("row", tn, k, self.raw(tn, k, vals)))

    def holders(self, fk, k):
        return sorted(self.held[fk.name].get(k, ()))

    def held_by_any(self, fk, k):
        return bool(self.held[fk.name].get(k))
