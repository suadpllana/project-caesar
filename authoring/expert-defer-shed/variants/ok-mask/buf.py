"""Buffers held as a bit per slot and a list kept in score order.

The free slots of an expert are the set bits of one integer, so the lowest free index is the
lowest set bit and taking or giving a slot back is one mask operation. The displaceable
occupants are (-score, slot, token) kept ascending, which puts the weakest - lowest score, and
the larger slot among equals - at the end, where a stale entry pops in constant time.
"""
import bisect


class Bufs:
    __slots__ = ("c", "hold", "freem", "weak")

    def __init__(self, ex, c):
        self.c = c
        self.hold = [{} for _ in range(ex)]
        self.freem = [(1 << c) - 1 for _ in range(ex)]
        self.weak = [[] for _ in range(ex)]

    def free(self, e):
        m = self.freem[e]
        return (m & -m).bit_length() - 1 if m else None

    def fill(self, e, tid, s):
        slot = self.free(e)
        self.freem[e] &= ~(1 << slot)
        self.hold[e][slot] = tid
        bisect.insort(self.weak[e], (-s, slot, tid))
        return slot

    def seize(self, e, slot, tid, s):
        self.hold[e][slot] = tid
        bisect.insort(self.weak[e], (-s, slot, tid))

    def drop(self, e, slot):
        del self.hold[e][slot]
        self.freem[e] |= 1 << slot

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
