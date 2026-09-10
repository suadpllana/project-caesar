import bisect


class Space:
    def __init__(self):
        self.cur = {}
        self.log = {}
        self.xs = {}
        self.n = 0

    def vol(self, v):
        self.xs[v] = []

    def mint(self):
        self.n += 1
        return self.n

    def now(self, v, x):
        return self.cur.get((v, x))

    def put(self, v, x, b, t):
        key = (v, x)
        rec = self.log.get(key)
        if rec is None:
            rec = ([], [])
            self.log[key] = rec
            self.xs[v].append(x)
        ts, bs = rec
        if ts and ts[-1] == t:
            bs[-1] = b
        else:
            ts.append(t)
            bs.append(b)
        if b is None:
            self.cur.pop(key, None)
        else:
            self.cur[key] = b

    def then(self, v, x, t):
        rec = self.log.get((v, x))
        if rec is None:
            return None
        ts, bs = rec
        i = bisect.bisect_right(ts, t) - 1
        if i < 0:
            return None
        return bs[i]
