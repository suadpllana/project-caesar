"""The waiting line: every difference the reader can voice, with its age.

A difference joins the line at the end of the tick that first observed it and keeps that age
while it persists, however often its text changes; a cut hands a carried difference back at the
age it had when the utterance took it. Held differences stay in the line but out of reach.

Selection is oldest first, assertive ahead of polite, ties to the lower text node id and then
the lower region id. Two heaps with lazy deletion give that in logarithmic time. An entry is
valid only while its key still has that age, is not held and still has that loudness; anything
else is thrown away when it surfaces. That is sound because a stale entry can only become valid
again through `put`, which pushes a fresh one anyway. Rescanning the line at every selection is
exactly as correct, and is what the held family is there to rule out.
"""
import heapq


class Line:
    def __init__(self):
        self.age = {}
        self.cls = {}
        self.held = set()
        self.heap = {"assertive": [], "polite": []}
        self.reg = {}
        self.anc = {}
        self.anchor = {}
        self.nod = {}

    def put(self, k, age, cls, held, anchor):
        r, n = k
        was = self.anchor.get(k)
        if was is not None and was != anchor:
            self._unanchor(k, was)
        self.age[k] = age
        self.cls[k] = cls
        self.reg.setdefault(r, set()).add(k)
        self.nod.setdefault(n, set()).add(r)
        if anchor is not None:
            self.anchor[k] = anchor
            self.anc.setdefault(anchor, set()).add(k)
        else:
            self.anchor.pop(k, None)
        if held:
            self.held.add(k)
        else:
            self.held.discard(k)
            heapq.heappush(self.heap[cls], (age, n, r))

    def hold(self, k, held):
        if k not in self.age:
            return
        if held:
            self.held.add(k)
        elif k in self.held:
            self.held.discard(k)
            r, n = k
            heapq.heappush(self.heap[self.cls[k]], (self.age[k], n, r))

    def _unanchor(self, k, a):
        s = self.anc.get(a)
        if s is not None:
            s.discard(k)
            if not s:
                del self.anc[a]

    def drop(self, k):
        if k not in self.age:
            return
        r, n = k
        del self.age[k]
        del self.cls[k]
        self.held.discard(k)
        s = self.reg.get(r)
        if s is not None:
            s.discard(k)
            if not s:
                del self.reg[r]
        s = self.nod.get(n)
        if s is not None:
            s.discard(r)
            if not s:
                del self.nod[n]
        a = self.anchor.pop(k, None)
        if a is not None:
            self._unanchor(k, a)

    def regions_of(self, n):
        return tuple(self.nod.get(n, ()))

    def of_region(self, r):
        return list(self.reg.get(r, ()))

    def anchored(self, a):
        return list(self.anc.get(a, ()))

    def ready(self, k):
        return k in self.age and k not in self.held

    def top(self, cls):
        pile = self.heap[cls]
        while pile:
            age, n, r = pile[0]
            k = (r, n)
            if self.age.get(k) == age and k not in self.held and self.cls.get(k) == cls:
                return k
            heapq.heappop(pile)
        return None
