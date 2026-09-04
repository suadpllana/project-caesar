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
            return h
        q = self.core.waiters(m)
        return q[0] if q else 0

    def debts(self):
        c = self.core
        out = []
        for m in c.locks():
            o = self.owner(m)
            if not o:
                continue
            for x in c.waiters(m):
                if x != o:
                    out.append((x, o))
        return out

    def settle(self):
        c = self.core
        ids = c.ids()
        val = {}
        for t in ids:
            val[t] = c.base[t]
        owed = [(x, o) for x, o in self.debts() if x in val and o in val]
        for _ in range(len(ids) + 1):
            moved = False
            for x, o in owed:
                if val[x] > val[o]:
                    val[o] = val[x]
                    moved = True
            if not moved:
                break
        for t in ids:
            c.set(t, val[t])
