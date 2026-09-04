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
        dep = {}
        for m in c.locks():
            q = c.waiters(m)
            if not q:
                continue
            h = c.holder(m)
            for i, w in enumerate(q):
                if h:
                    dep.setdefault(h, []).append(w)
                for a in q[:i]:
                    dep.setdefault(a, []).append(w)
        return dep

    def settle(self):
        c = self.core
        dep = self.owed()
        ids = c.ids()
        val = {}
        for t in ids:
            val[t] = c.base[t]
        for _ in range(len(ids) + 2):
            moved = False
            for t in ids:
                p = c.base[t]
                for w in dep.get(t, ()):
                    if val[w] > p:
                        p = val[w]
                if p > val[t]:
                    val[t] = p
                    moved = True
            if not moved:
                break
        for t in ids:
            c.set(t, val[t])
