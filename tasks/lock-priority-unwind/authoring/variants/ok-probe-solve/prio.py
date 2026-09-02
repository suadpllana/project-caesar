class Prio:
    def __init__(self, core):
        self.core = core

    def blocked(self, w, m, h):
        self.sync()

    def granted(self, t, m):
        self.sync()

    def released(self, t, m):
        self.sync()

    def expired(self, w, m, h):
        self.sync()

    def sync(self):
        c = self.core
        waiters = {}
        for m in sorted(c.ms):
            mx = c.ms[m]
            h = mx.h
            if not h:
                continue
            for w in mx.w:
                if w == h:
                    continue
                waiters.setdefault(h, []).append(w)

        memo = {}
        for t in c.ids():
            c.set(t, self.value(t, waiters, memo, set()))

    def value(self, t, waiters, memo, path):
        if t in memo:
            return memo[t]
        if t in path:
            return self.core.base.get(t, 0)
        best = self.core.base.get(t, 0)
        path.add(t)
        for w in waiters.get(t, ()):
            v = self.value(w, waiters, memo, path)
            if v > best:
                best = v
        path.discard(t)
        if not path:
            memo[t] = best
        return best
