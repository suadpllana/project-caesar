"""An alternative correct policy: push from the queues rather than pull from the tasks.

The reference asks each task what is waiting on it. This walks the mutexes instead and pushes
each queue's urgency onto whatever that queue is waiting for - the holder, or the task at the
head of it while the mutex is between owners - and repeats until nothing moves. Same least
fixed point, opposite direction of travel.
"""


class Prio:
    def __init__(self, core):
        self.core = core

    def blocked(self, w, m, h):
        self.relax()

    def released(self, t, m):
        self.relax()

    def expired(self, w, m, h):
        self.relax()

    def relax(self):
        c = self.core
        for t in c.ids():
            c.set(t, c.base[t])
        for _ in range(len(c.ids()) + 2):
            moved = False
            for m in c.locks():
                q = c.waiters(m)
                if not q:
                    continue
                h = c.holder(m)
                if h:
                    pool, target = q, h
                else:
                    pool, target = q[1:], q[0]
                for x in pool:
                    if c.eff[x] > c.eff[target]:
                        c.set(target, c.eff[x])
                        moved = True
            if not moved:
                return
