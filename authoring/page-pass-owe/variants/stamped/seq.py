"""View as a sorted key list per tag with a sorted id list under each key."""

import bisect


class View(object):
    def __init__(self):
        self.keys = {}
        self.ids = {}

    def places(self, g):
        out = []
        for k in self.keys.get(g, ()):
            for i in self.ids[g][k]:
                out.append((k, i))
        return out

    def put(self, k, i, g):
        ks = self.keys.setdefault(g, [])
        pool = self.ids.setdefault(g, {})
        at = bisect.bisect_left(ks, k)
        if at == len(ks) or ks[at] != k:
            ks.insert(at, k)
            pool[k] = []
        bisect.insort(pool[k], i)

    def take(self, k, i, g):
        pool = self.ids.get(g)
        if not pool or k not in pool:
            return
        row = pool[k]
        at = bisect.bisect_left(row, i)
        if at < len(row) and row[at] == i:
            del row[at]
        if not row:
            del pool[k]
            ks = self.keys[g]
            at = bisect.bisect_left(ks, k)
            if at < len(ks) and ks[at] == k:
                del ks[at]

    def walk(self, g, mk):
        ks = self.keys.get(g)
        if not ks:
            return
        pool = self.ids[g]
        if mk is None:
            kat, iat = 0, 0
        else:
            kat = bisect.bisect_left(ks, mk[0])
            if kat < len(ks) and ks[kat] == mk[0]:
                iat = bisect.bisect_right(pool[mk[0]], mk[1])
            else:
                iat = 0
        while kat < len(ks):
            k = ks[kat]
            row = pool[k]
            while iat < len(row):
                yield (k, row[iat])
                iat += 1
            kat += 1
            iat = 0

    def members(self, g):
        for k in self.keys.get(g, ()):
            for i in self.ids[g][k]:
                yield i
