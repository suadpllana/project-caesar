"""An alternative correct policy: solve the whole assignment rather than patch it.

Where the reference walks up from the task that changed, this recomputes every task in the
system to a fixed point whenever anything happens. It is more work per event and reaches the
same assignment, which is the point of keeping it: the schedule is a property of the rule, not
of how the rule is applied.
"""


class Prio:
    def __init__(self, core):
        self.core = core

    def blocked(self, w, m, h):
        self.solve()

    def granted(self, t, m):
        self.solve()

    def released(self, t, m):
        self.solve()

    def expired(self, w, m, h):
        self.solve()

    def solve(self):
        c = self.core
        for t in c.ids():
            c.set(t, c.base[t])
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
