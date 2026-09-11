"""Correct, and the dumbest reading of the contract: one cell per slot."""


class Cell:
    def __init__(self, n):
        self.n = n
        self.live = True
        self.mi = -1
        self.since = 0
        self.warm = False
        self.v = [0] * n
        self.m = [0] * n
        self.g = [0] * n

    def runs(self, f):
        arr = self.v if f == 0 else self.m
        out = []
        for x in arr:
            if out and out[-1][1] == x:
                out[-1][0] += 1
            else:
                out.append([1, x])
        return [(c, x) for c, x in out]

    def take(self, k):
        g = self.g
        for i in range(self.n):
            g[i] += k
        self.warm = any(g)

    def chill(self):
        self.m = [0] * self.n

    def spend(self, lo, hi, left):
        used = 0
        stop = False
        for i in range(lo, hi):
            g = self.g[i]
            if g == 0:
                continue
            cost = -g if g < 0 else g
            if used + cost > left:
                stop = True
                break
            used += cost
            self.m[i] += g
            self.v[i] -= self.m[i]
            self.g[i] = 0
        self.warm = any(self.g)
        return used, stop

    def keep(self):
        return [(1, self.v[i], self.m[i]) for i in range(self.n)]

    def put(self, runs):
        i = 0
        for c, v, m in runs:
            for _ in range(c):
                self.v[i] = v
                self.m[i] = m
                i += 1
