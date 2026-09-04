class Prio:
    # What a task is worth is not patched at each event, it is derived from the
    # state the core is in.  For every task t:
    #
    #     eff(t) = max(base(t), max eff(x) for every x standing behind t)
    #
    # and x stands behind t when x is queued on a mutex that t holds, or when x
    # is queued on a mutex behind t in that queue.  Handover is strictly first
    # in first out, so a task queued ahead of x is as much in x's way as the
    # holder is, and it has to be lent enough to get out of the way.  The value
    # taken is the least one satisfying that, so no task is ever worth more than
    # something still waiting behind it can account for.
    #
    # Deriving instead of patching is what covers the moments the core does not
    # hand over.  Taking a mutex leaves the relation alone: the taker was in
    # front of the rest of the queue as its head and is in front of them as the
    # holder, so nothing is owed at that instant and no call is needed for it.

    def __init__(self, core):
        self.core = core

    def blocked(self, w, m, h):
        self.settle()

    def released(self, t, m):
        self.settle()

    def expired(self, w, m, h):
        self.settle()

    def fronts(self):
        out = []
        for m in self.core.locks():
            h = self.core.holder(m)
            q = self.core.waiters(m)
            for i, x in enumerate(q):
                if h and h != x:
                    out.append((h, x))
                for j in range(i):
                    if q[j] != x:
                        out.append((q[j], x))
        return out

    def want(self):
        v = {}
        for t in self.core.ids():
            v[t] = self.core.base[t]
        e = self.fronts()
        n = len(v) + 1
        while n > 0:
            n -= 1
            moved = False
            for f, x in e:
                if f in v and x in v and v[f] < v[x]:
                    v[f] = v[x]
                    moved = True
            if not moved:
                break
        return v

    def settle(self):
        v = self.want()
        for t in self.core.ids():
            if self.core.eff[t] != v[t]:
                self.core.set(t, v[t])
