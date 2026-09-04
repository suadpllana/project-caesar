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
            tgt = c.holder(m)
            if not tgt:
                tgt = q[0]
                q = q[1:]
            for w in q:
                if w != tgt:
                    out.append((w, tgt))
        return out

    def settle(self):
        c = self.core
        ids = c.ids()
        val = {}
        for t in ids:
            val[t] = c.base[t]
        link = self.owed()
        for _ in range(len(ids) + 2):
            moved = False
            for w, tgt in link:
                if w in val and tgt in val and val[w] > val[tgt]:
                    val[tgt] = val[w]
                    moved = True
            if not moved:
                break
        for t in ids:
            c.set(t, val[t])
