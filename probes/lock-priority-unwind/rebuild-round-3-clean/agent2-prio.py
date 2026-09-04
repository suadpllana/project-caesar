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
            x = c.ms[m]
            o = x.h
            q = list(x.w)
            if o == 0:
                if not q:
                    continue
                o = q[0]
                q = q[1:]
            for t in q:
                if t != o:
                    out.append((o, t))
        return out

    def settle(self):
        c = self.core
        ids = c.ids()
        val = {}
        for t in ids:
            val[t] = c.base[t]
        owed = self.owed()
        for _ in range(len(ids) + 1):
            moved = False
            for o, t in owed:
                if o in val and t in val and val[t] > val[o]:
                    val[o] = val[t]
                    moved = True
            if not moved:
                break
        for t in ids:
            c.set(t, val[t])
