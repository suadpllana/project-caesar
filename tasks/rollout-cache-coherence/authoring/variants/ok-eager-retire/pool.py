"""Reference page pool.

The shipped file loses the discard on a level 2 wake: the pages come back mapped, so
usable() says yes, while what they hold is whatever the allocator handed back.  The
block table then keeps serving blocks whose contents were thrown away, and the index
keeps advertising them - the two halves disagree about the same page.

The fix is to record which pages actually lost their contents and to keep saying no
about them until they are handed out again.  Only pages that were mapped at the time of
the sleep are marked; free pages hold nothing worth losing.  A level 1 sleep copies the
pages out and back, so nothing is marked and every cached block survives the cycle.
"""

from model.arch import D, L, M

ZERO = tuple([0] * D)
JUNK = tuple([(M - 7)] * D)


def blank(bs):
    return [tuple([(ZERO, ZERO)] * L) for _ in range(bs)]


def junk(bs):
    return [tuple([(JUNK, JUNK)] * L) for _ in range(bs)]


class Pool:
    def __init__(self, npages, bs):
        self.bs = bs
        self.pg = {}
        self.free = []
        for i in range(npages):
            self.pg[i] = blank(bs)
            self.free.append(i)
        self.lvl = 0
        self.off = {}
        self.dead = set()

    def take(self):
        if not self.free:
            return None
        pid = self.free.pop(0)
        self.dead.discard(pid)
        return pid

    def give(self, pid):
        self.pg[pid] = blank(self.bs)
        self.dead.discard(pid)
        if pid not in self.free:
            self.free.append(pid)

    def write(self, pid, slot, kv):
        self.pg[pid][slot] = tuple(kv)

    def read(self, pid, slot):
        return self.pg[pid][slot]

    def usable(self, pid):
        return pid in self.pg and pid not in self.dead

    def sleep(self, lvl):
        self.lvl = lvl
        if lvl == 1:
            self.off = {p: self.pg[p] for p in self.pg}
        self.pg = {p: None for p in self.pg}

    def wake(self):
        if self.lvl == 1 and self.off:
            for p, d in self.off.items():
                self.pg[p] = d
            self.off = {}
        else:
            for p in list(self.pg):
                self.pg[p] = junk(self.bs)
                if p not in self.free:
                    self.dead.add(p)
        self.lvl = 0
