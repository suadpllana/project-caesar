class Prio:
    """What a task is worth is a pure function of the mutex state.

    A task is worth its own base priority, or the most urgent thing queued behind it,
    whichever is greater, followed up the chain: a task queued behind a task that is
    itself queued behind a third lends its urgency to all of them.

    The task standing between a waiter and a mutex is the holder if the mutex has one.
    If it does not, it is the head of the queue: core.py hands a released mutex to
    whoever has been queued longest and lets nobody else take it, so the head is the
    only task that can clear the way, whether or not it has picked the mutex up yet.
    Reading it that way also makes the value survive the pick-up, which matters because
    core.py does not call us there.

    Every one of the three moments changes only the queues and the holders, so rather
    than patch the value at each one, settle recomputes the whole table from the state
    that is there now.  A task that has nothing behind it any more falls back to its
    own priority by construction.
    """

    def __init__(self, core):
        self.core = core

    def blocked(self, w, m, h):
        self.settle()

    def released(self, t, m):
        self.settle()

    def expired(self, w, m, h):
        self.settle()

    def owner(self, m):
        c = self.core
        h = c.holder(m)
        if h:
            return h
        q = c.waiters(m)
        return q[0] if q else 0

    def debts(self):
        c = self.core
        out = []
        for m in c.locks():
            d = self.owner(m)
            if not d:
                continue
            for x in c.waiters(m):
                if x != d:
                    out.append((x, d))
        return out

    def settle(self):
        c = self.core
        ids = c.ids()
        val = {}
        for t in ids:
            val[t] = c.base[t]
        link = self.debts()
        guard = 0
        cap = len(ids) + 2
        while guard < cap:
            guard += 1
            moved = False
            for x, d in link:
                if val.get(x, 0) > val.get(d, 0):
                    val[d] = val[x]
                    moved = True
            if not moved:
                break
        for t in ids:
            c.set(t, val[t])
