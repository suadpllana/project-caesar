"""An alternative correct policy: one call, relaxing only the tasks anybody is waiting for.

Every event funnels into the same routine, because every event is the same question: has the
set of tasks waiting on somebody changed. Rather than touching every task, this collects the
tasks that currently have a queue behind them - holders, and the tasks at the head of a mutex
between owners - and relaxes those until the assignment stops moving.
"""


class Prio:
    def __init__(self, core):
        self.core = core

    def blocked(self, w, m, h):
        self.sync()

    def released(self, t, m):
        self.sync()

    def expired(self, w, m, h):
        self.sync()

    def owing(self):
        c = self.core
        pairs = {}
        for m in c.locks():
            q = c.waiters(m)
            if not q:
                continue
            h = c.holder(m)
            if h:
                pairs.setdefault(h, []).extend(q)
            else:
                pairs.setdefault(q[0], []).extend(q[1:])
        return pairs

    def sync(self):
        c = self.core
        for t in c.ids():
            c.set(t, c.base[t])
        for _ in range(len(c.ids()) + 2):
            pairs = self.owing()
            moved = False
            for t in sorted(pairs):
                p = c.base[t]
                for w in pairs[t]:
                    if c.eff[w] > p:
                        p = c.eff[w]
                if p != c.eff[t]:
                    c.set(t, p)
                    moved = True
            if not moved:
                return
