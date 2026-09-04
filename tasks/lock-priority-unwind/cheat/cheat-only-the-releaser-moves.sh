#!/bin/bash
# Reads a release as one thing happening to one task. Two tasks move at a release: the one letting go falls, and the one at the head of the queue rises to whatever is waiting behind it.
set -euo pipefail

mkdir -p "$(dirname /app/rt/prio.py)"
cat > /app/rt/prio.py <<'EOF_PRIO'
"""What a task has to be worth while somebody else is waiting on it.

The rule the requirement asks for is one sentence: a task is worth its own priority, or the
most urgent thing that is waiting for it, whichever is greater, and that has to hold all the
way along a chain of waiting. Getting there is two separate pieces of work, and only the first
one is the piece every account of priority inversion covers.

The first piece is that the four rules are one quantity. Raise on block and put the holder back
on release is right for one mutex and one waiter and wrong for everything else: a holder of two
mutexes that is put back to its own priority abandons whoever is still queued on the other, a
waiter can block on a holder that is itself blocked so the urgency has to travel the whole
chain, and a wait that runs out stops being a reason for anybody to be urgent. All four moments
change the same set, so all of them call the same recomputation and it walks up the chain until
it stops making a difference.

The second piece is the one the write ups do not have, and it comes out of rt/core.py rather
than out of the rule. A mutex is not handed over when it is let go. Releasing it leaves it
free, and the task at the head of its queue is woken and is the only task allowed to take it -
it takes it later, when the scheduler next picks it. For as long as that lasts, the tasks
behind it are waiting for a task that holds nothing at all. So "who is waiting for me" is not
"who is queued on what I hold": it is who is queued on what I hold, plus everybody behind me on
a mutex that is free and mine to take. A policy that reads holders gives that task its own
priority, it does not get the processor, and the queue behind it sits there - which is the same
inversion the boost exists to prevent, now caused by the boost being aimed at nobody.

The same fact breaks the chain walk. What a waiter is waiting for is the holder of the mutex it
is queued on, and while that mutex is free it is the task at the head of the queue instead. A
walk that follows holders stops dead at a mutex that is between owners, so the fall never
reaches the task that is actually running.

And it is why a release moves two tasks rather than one. The task letting go falls to whatever
is still waiting on what it still holds; the task at the head of the queue rises to whatever is
waiting behind it. One moment, two answers, opposite directions.
"""


class Prio:
    def __init__(self, core):
        self.core = core

    def blocked(self, w, m, h):
        self.settle(self.next_up(m))

    def released(self, t, m):
        self.settle(t)

    def expired(self, w, m, h):
        self.settle(self.next_up(m))

    def next_up(self, m):
        """The task the queue on m is waiting for: its holder, or the one about to take it."""
        h = self.core.holder(m)
        if h:
            return h
        q = self.core.waiters(m)
        return q[0] if q else 0

    def owed(self, t):
        """t's own priority, or the most urgent thing waiting for t, whichever is greater."""
        c = self.core
        p = c.base[t]
        for m in c.locks():
            q = c.waiters(m)
            if c.holder(m) == t:
                pass
            elif c.holder(m) == 0 and q and q[0] == t:
                q = q[1:]
            else:
                continue
            for x in q:
                if c.eff[x] > p:
                    p = c.eff[x]
        return p

    def upstream(self, t):
        """Whoever t is itself waiting for, which is nobody once t is the one about to take it."""
        c = self.core
        m = c.blocking(t)
        if not m:
            return 0
        h = c.holder(m)
        if h:
            return h
        q = c.waiters(m)
        return q[0] if q and q[0] != t else 0

    def settle(self, t):
        """Recompute t, and keep going while the answer changes for whoever t waits for."""
        seen = 0
        while t and seen < 64:
            seen += 1
            p = self.owed(t)
            if p == self.core.eff[t]:
                return
            self.core.set(t, p)
            t = self.upstream(t)
EOF_PRIO
