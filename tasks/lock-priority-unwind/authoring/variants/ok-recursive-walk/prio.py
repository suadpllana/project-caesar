"""An alternative correct policy: the same walk, expressed as a recursion.

The reference loops up the chain. This calls itself on whoever the task it just changed is
waiting for, and stops when the answer stops moving. Identical assignment, different shape.
"""


class Prio:
    def __init__(self, core):
        self.core = core

    def blocked(self, w, m, h):
        self.settle(self.ahead(m), 0)

    def released(self, t, m):
        self.settle(t, 0)
        self.settle(self.ahead(m), 0)

    def expired(self, w, m, h):
        self.settle(self.ahead(m), 0)

    def ahead(self, m):
        h = self.core.holder(m)
        if h:
            return h
        q = self.core.waiters(m)
        return q[0] if q else 0

    def behind(self, t):
        c = self.core
        out = []
        for m in c.locks():
            q = c.waiters(m)
            if c.holder(m) == t:
                out.extend(q)
            elif c.holder(m) == 0 and q and q[0] == t:
                out.extend(q[1:])
        return out

    def settle(self, t, depth):
        if not t or depth > 64:
            return
        c = self.core
        p = c.base[t]
        for w in self.behind(t):
            if c.eff[w] > p:
                p = c.eff[w]
        if p == c.eff[t]:
            return
        c.set(t, p)
        m = c.blocking(t)
        if not m:
            return
        nxt = self.ahead(m)
        self.settle(nxt if nxt != t else 0, depth + 1)
