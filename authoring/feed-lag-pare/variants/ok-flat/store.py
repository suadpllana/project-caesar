import bisect


class Store:
    def __init__(self):
        self.ent = {}
        self.idx = {}
        self.head = 0
        self.live = 0
        self.tab = {}
        self.dirty = set()

    def append(self, kind, key, arg):
        self.head += 1
        self.ent[self.head] = (kind, key, arg)
        self.idx.setdefault(key, []).append(self.head)
        self.live += 1
        self.dirty.add(key)
        return self.head

    def drop(self, seq):
        _kind, key, _arg = self.ent.pop(seq)
        row = self.idx[key]
        row.pop(bisect.bisect_left(row, seq))
        if not row:
            del self.idx[key]
        self.live -= 1
        self.dirty.add(key)

    def put(self, seq, kind, key, arg):
        self.ent[seq] = (kind, key, arg)
        self.dirty.add(key)

    def count(self):
        return self.live

    def entry(self, seq):
        return self.ent[seq]

    def at(self, key, floor, top):
        row = self.idx.get(key)
        if not row:
            return []
        return row[bisect.bisect_right(row, floor):bisect.bisect_right(row, top)]

    def keys(self):
        return sorted(self.idx)

    def items(self):
        return [(s,) + self.ent[s] for s in sorted(self.ent)]

    def soil(self, lo, hi):
        if hi - lo >= len(self.idx):
            self.dirty.update(self.idx)
            return
        for key in range(lo, hi + 1):
            if key in self.idx:
                self.dirty.add(key)

    def soil_all(self):
        self.dirty.update(self.idx)
