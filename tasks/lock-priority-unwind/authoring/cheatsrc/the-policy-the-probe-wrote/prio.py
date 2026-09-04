class Prio:
    def __init__(self, core):
        self.core = core

    def blocked(self, w, m, h):
        self.solve()

    def released(self, t, m):
        self.solve()

    def expired(self, w, m, h):
        self.solve()

    def solve(self):
        c = self.core
        for _ in range(len(c.ids()) + 2):
            moved = False
            for t in c.ids():
                p = c.base[t]
                for m in c.held(t):
                    for w in c.waiters(m):
                        if c.eff[w] > p:
                            p = c.eff[w]
                if p != c.eff[t]:
                    c.set(t, p)
                    moved = True
            if not moved:
                return
