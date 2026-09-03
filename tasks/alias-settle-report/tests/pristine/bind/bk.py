class Book(object):
    def __init__(self, sp):
        self.keys = set(sp.watch)
        for pool in sp.runs.values():
            self.keys.update(pool)
        for pool in sp.tags.values():
            self.keys.update(pool)
        self.up = dict((k, k) for k in self.keys)
        self.wt = dict((k, 1) for k in self.keys)
        self.bars = set()
        self.post = {}
        self.runs = dict((n, sorted(p)) for n, p in sp.runs.items())
        self.tags = dict((n, sorted(p)) for n, p in sp.tags.items())
        self.live = set(self.runs) | set(self.tags)
        self.watch = list(sp.watch)
        self.filed = set()

    def find(self, k):
        r = k
        while self.up[r] != r:
            r = self.up[r]
        while self.up[k] != r:
            self.up[k], k = r, self.up[k]
        return r

    def weld(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return
        if self.wt[ra] < self.wt[rb]:
            ra, rb = rb, ra
        self.up[rb] = ra
        self.wt[ra] += self.wt[rb]

    def cells(self):
        out = {}
        for k in sorted(self.keys):
            out.setdefault(self.find(k), []).append(k)
        return out

    def held(self, c):
        return [k for k in sorted(self.keys) if self.find(k) == c]

    def open_tags(self):
        return sorted(n for n in self.tags if n in self.live)

    def open_runs(self):
        return sorted(n for n in self.runs if n in self.live)

    def unsent(self, n):
        return [k for k in self.runs[n] if (n, k) not in self.post]
