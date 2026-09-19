"""Expert buffers, held as slots rather than as a count.

Two things free a slot in the middle of a step: a displacement takes away every placement the
occupant holds from that rank on, and the next arrival at that expert fills the lowest index
that is free rather than the next one never used. A counter cannot say either, so a buffer is
a slot map with the returned indices kept in order beside it.

The order over displaceable occupants is a heap with lazy deletion, and that is affordable
because of the step's own invariant: a token is displaced at most once, so an entry that has
stopped being valid can never become valid again and is thrown away the moment it surfaces.
Scanning the buffer for the weakest occupant is exactly as correct and is what the wide
programs are there to rule out.
"""
import heapq


class Bufs:
    __slots__ = ("c", "hold", "nxt", "back", "weak")

    def __init__(self, ex, c):
        self.c = c
        self.hold = [{} for _ in range(ex)]
        self.nxt = [0] * ex
        self.back = [[] for _ in range(ex)]
        self.weak = [[] for _ in range(ex)]

    def free(self, e):
        """The lowest free slot index of e, or None when the buffer is full."""
        if self.back[e]:
            return self.back[e][0]
        return self.nxt[e] if self.nxt[e] < self.c else None

    def fill(self, e, token, weight):
        """Put token in the lowest free slot. The caller has checked there is one."""
        if self.back[e]:
            slot = heapq.heappop(self.back[e])
        else:
            slot = self.nxt[e]
            self.nxt[e] += 1
        self.hold[e][slot] = token
        heapq.heappush(self.weak[e], (weight, -slot, token))
        return slot

    def seize(self, e, slot, token, weight):
        """Hand an occupied slot straight to token: the slot never becomes free."""
        self.hold[e][slot] = token
        heapq.heappush(self.weak[e], (weight, -slot, token))

    def drop(self, e, slot):
        del self.hold[e][slot]
        heapq.heappush(self.back[e], slot)

    def weakest(self, e, gone):
        """Lowest-scoring occupant not yet displaced this step, ties to the larger slot."""
        pile = self.weak[e]
        while pile:
            weight, negslot, token = pile[0]
            slot = -negslot
            if self.hold[e].get(slot) == token and not gone[token]:
                return weight, slot, token
            heapq.heappop(pile)
        return None

    def count(self, e):
        return len(self.hold[e])

    def at(self, e):
        return self.hold[e]
