"""An alternative correct policy: relax the holders until nothing moves.

Where the reference walks upward from whatever changed, and the full solve touches every task,
this touches only the tasks that are holding something and relaxes them repeatedly until the
assignment stops changing. Every event funnels into the same call, because every event is the
same question: has the set of tasks waiting on somebody changed.
"""


class Prio:
    def __init__(self, core):
        self.core = core

    def blocked(self, w, m, h):
        self.relax()

    def granted(self, t, m):
        self.relax()

    def released(self, t, m):
        self.relax()

    def expired(self, w, m, h):
        self.relax()

    def relax(self):
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
