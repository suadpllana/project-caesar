"""What a task's priority has to be while it is holding something somebody else needs.

The shipped policy is the one every introduction to this writes down, and it is right about
exactly one shape: a single mutex, one waiter, one holder. Raise the holder when a more urgent
task blocks on it, put the holder back on release. Everything past that shape it gets wrong,
and the two ways it gets it wrong are different from each other.

It is wrong on release, because a holder can hold more than one thing. Putting it back to its
own priority the moment it releases one mutex abandons whoever is still waiting on the others,
and the task that was donating urgency a tick ago is now the lowest thing in the system with a
queue behind it. What it has to go back to is not where it started; it is whatever the tasks
still waiting on the mutexes it still holds are worth.

It is wrong on the way up, because blocking is not one deep. The task a waiter blocks on can
itself be blocked on something else, and the urgency has to travel the whole way along that
chain or it stops at the first link and the task actually holding the CPU never hears about
it.

Both of those are the same computation run in two directions, which is why this is one
function and not four. A task is worth its own priority, or the most urgent thing waiting on
anything it holds, whichever is greater. Whenever that changes for a task, it can change for
whoever that task is itself waiting on, so the recomputation walks up the chain until it stops
making a difference.

Four moments can change it and all four are handled by the same walk. Somebody blocks. A mutex
is handed to a new holder that still has a queue behind it. A mutex is released. And a waiter
gives up and stops waiting, which lowers the holder rather than raising it, and is the one
that gets left out - a timeout is a change to the same set the other three read, so it moves
the same numbers.
"""


class Prio:
    def __init__(self, core):
        self.core = core

    def blocked(self, w, m, h):
        self.settle(h)

    def granted(self, t, m):
        self.settle(t)

    def released(self, t, m):
        self.settle(t)

    def expired(self, w, m, h):
        self.settle(h)

    def want(self, t):
        """A task is worth its own priority, or the most urgent thing waiting on it."""
        p = self.core.base[t]
        for m in self.core.held(t):
            if self.core.waiters(m):
                for u in self.core.ids():
                    if self.core.base[u] > p:
                        p = self.core.base[u]
        return p

    def settle(self, t):
        """Recompute t, and keep going while the answer changes for whoever t waits on."""
        seen = 0
        while t and seen < 64:
            seen += 1
            p = self.want(t)
            if p == self.core.eff[t]:
                return
            self.core.set(t, p)
            t = self.core.holder(self.core.blocking(t))
