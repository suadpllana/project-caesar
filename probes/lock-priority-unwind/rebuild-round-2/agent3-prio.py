class Prio:
    def __init__(self, core):
        self.core = core

    def blocked(self, w, m, h):
        self.settle()

    def released(self, t, m):
        self.settle()

    def expired(self, w, m, h):
        self.settle()

    def debts(self):
        c = self.core
        d = {}
        for m in c.locks():
            q = c.waiters(m)
            o = c.holder(m)
            if o == 0:
                if not q:
                    continue
                o = q[0]
            for x in q:
                if x != o:
                    d.setdefault(o, []).append(x)
        return d

    def settle(self):
        c = self.core
        ids = c.ids()
        val = {}
        for t in ids:
            val[t] = c.base[t]
        d = self.debts()
        who = sorted(d)
        n = len(ids) + 2
        while n > 0:
            n -= 1
            calm = True
            for o in who:
                if o not in val:
                    continue
                v = val[o]
                for x in d[o]:
                    if x in val and val[x] > v:
                        v = val[x]
                if v > val[o]:
                    val[o] = v
                    calm = False
            if calm:
                break
        for t in ids:
            c.set(t, val[t])
