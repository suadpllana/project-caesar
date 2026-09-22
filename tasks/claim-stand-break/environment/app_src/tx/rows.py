import bisect


class Rows:
    __slots__ = ("ver", "vs", "xs", "keys")

    def __init__(self):
        self.ver = 0
        self.vs = {}
        self.xs = {}
        self.keys = []

    def at(self, key, ver):
        vs = self.vs.get(key)
        if not vs:
            return None
        i = bisect.bisect_right(vs, ver)
        if not i:
            return None
        return self.xs[key][i - 1]

    def after(self, key, base):
        vs = self.vs.get(key)
        return bool(vs) and vs[-1] > base

    def put(self, ch):
        self.ver += 1
        for key in sorted(ch):
            val = ch[key]
            if self.at(key, self.ver) == val:
                continue
            vs = self.vs.get(key)
            if vs is None:
                self.vs[key] = [self.ver]
                self.xs[key] = [val]
                bisect.insort(self.keys, key)
            else:
                vs.append(self.ver)
                self.xs[key].append(val)
        return self.ver

    def span(self, lo, hi):
        keys = self.keys
        i = bisect.bisect_left(keys, lo)
        n = len(keys)
        while i < n and keys[i] <= hi:
            yield keys[i]
            i += 1

    def live(self, lo, hi):
        got = []
        ver = self.ver
        for key in self.span(lo, hi):
            val = self.at(key, ver)
            if val is not None:
                got.append((key, val))
        return got
