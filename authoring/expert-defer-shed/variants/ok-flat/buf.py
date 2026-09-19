"""Buffers with the free slots as a list kept in descending order.

Slot indices are stored negated and ascending, so the lowest free slot sits at the end of the
list: taking one is a pop and giving one back is an insort, both without a heap. The order over
displaceable occupants is a list of (-score, slot) kept ascending, whose last element is the
weakest with the larger slot among equals.
"""
import bisect


class Bufs:
    __slots__ = ("c", "hold", "spare", "weak")

    def __init__(self, ex, c):
        self.c = c
        self.hold = [{} for _ in range(ex)]
        self.spare = [list(range(-(c - 1), 1)) for _ in range(ex)] if c else \
                     [[] for _ in range(ex)]
        self.weak = [[] for _ in range(ex)]

    def free(self, e):
        row = self.spare[e]
        return -row[-1] if row else None

    def fill(self, e, tid, s):
        slot = -self.spare[e].pop()
        self.hold[e][slot] = tid
        bisect.insort(self.weak[e], (-s, slot, tid))
        return slot

    def seize(self, e, slot, tid, s):
        self.hold[e][slot] = tid
        bisect.insort(self.weak[e], (-s, slot, tid))

    def drop(self, e, slot):
        del self.hold[e][slot]
        bisect.insort(self.spare[e], -slot)

    def weakest(self, e, gone):
        row = self.weak[e]
        while row:
            negs, slot, tid = row[-1]
            if self.hold[e].get(slot) == tid and not gone[tid]:
                return -negs, slot, tid
            row.pop()
        return None

    def count(self, e):
        return len(self.hold[e])

    def at(self, e):
        return self.hold[e]
