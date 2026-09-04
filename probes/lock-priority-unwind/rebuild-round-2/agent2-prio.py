class Prio:
    def __init__(self, core):
        self.core = core

    def blocked(self, w, m, h):
        self.settle()

    def released(self, t, m):
        self.settle()

    def expired(self, w, m, h):
        self.settle()

    def owed(self):
        c = self.core
        out = []
        for m in c.locks():
            q = c.waiters(m)
            if not q:
                continue
            h = c.holder(m)
            if h:
                for w in q:
                    out.append((w, h))
            else:
                for w in q[1:]:
                    out.append((w, q[0]))
        return out

    def settle(self):
        c = self.core
        ids = c.ids()
        val = {}
        for t in ids:
            val[t] = c.base[t]
        debt = self.owed()
        for _ in range(len(ids) + 1):
            moved = False
            for w, o in debt:
                if val.get(w, 0) > val.get(o, 0):
                    val[o] = val[w]
                    moved = True
            if not moved:
                break
        for t in ids:
            c.set(t, val[t])
