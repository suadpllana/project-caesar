import copy


class Heap:
    def __init__(self, cat, rows):
        self.cat = cat
        self.t = {n: {} for n in cat.tables}
        for tn, k, vals in rows:
            self.t[tn][k] = list(vals)

    def get(self, tn, k):
        return self.t[tn].get(k)

    def has(self, tn, k):
        return k in self.t[tn]

    def put(self, tn, k, vals):
        self.t[tn][k] = list(vals)

    def drop(self, tn, k):
        return self.t[tn].pop(k, None)

    def keys(self, tn):
        return sorted(self.t[tn])

    def holders(self, fk, k):
        i = self.cat.tables[fk.table].pos[fk.col]
        return sorted(kk for kk, r in self.t[fk.table].items() if r[i] == k)

    def snap(self):
        return copy.deepcopy(self.t)

    def load(self, snap):
        self.t = copy.deepcopy(snap)
