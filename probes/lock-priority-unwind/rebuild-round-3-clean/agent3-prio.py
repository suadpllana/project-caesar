class Prio:
    def __init__(self, core):
        self.core = core

    def blocked(self, w, m, h):
        self.settle()

    def released(self, t, m):
        self.settle()

    def expired(self, w, m, h):
        self.settle()

    def owner(self, m):
        h = self.core.holder(m)
        if h:
            return h, self.core.waiters(m)
        q = self.core.waiters(m)
        if q:
            return q[0], q[1:]
        return 0, []

    def settle(self):
        c = self.core
        ids = c.ids()
        want = {}
        for t in ids:
            want[t] = c.base[t]
        n = len(ids) + 2
        for _ in range(n):
            moved = False
            for m in c.locks():
                o, q = self.owner(m)
                if not o or not q:
                    continue
                top = want[o]
                for x in q:
                    if want.get(x, 0) > top:
                        top = want[x]
                if top > want[o]:
                    want[o] = top
                    moved = True
            if not moved:
                break
        for t in ids:
            c.set(t, want[t])
