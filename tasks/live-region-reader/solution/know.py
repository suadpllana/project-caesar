"""What the reader believes, and what the utterance it is playing will teach it.

Belief is kept per (region element, text node): the text the reader believes is there, and the
anchor - the parent the node had when that entry was written. Keying by region is what lets a
node that moved between two regions be a removal in one and an addition in the other, with
separate fates. The anchor is deliberately not refreshed by a move inside a region: a move there
is no difference, so nothing is spoken and nothing is learned, and a later removal is placed
where the listener last believed the node was.

The playing utterance's carried values sit on top of belief, never inside it. That is the whole
point of the layer: the listener learns them only when the utterance finishes, a cut throws them
away, and until one of those happens a difference is measured against what the reader *will*
believe - `expect`.
"""


class Know:
    def __init__(self):
        self.b = {}
        self.carry = {}
        self.at = {}

    def _note(self, k):
        r, n = k
        if k in self.b or k in self.carry:
            self.at.setdefault(n, set()).add(r)
        else:
            s = self.at.get(n)
            if s is not None:
                s.discard(r)
                if not s:
                    del self.at[n]

    def load(self, entries):
        for k, v in entries.items():
            self.b[k] = v
            self._note(k)

    def expect(self, k):
        got = self.carry.get(k)
        if got is not None:
            return got[0]
        return self.b.get(k)

    def believe(self, k, v):
        if v is None:
            self.b.pop(k, None)
        else:
            self.b[k] = v
        self._note(k)

    def absorb(self, k, v):
        """Believe the current value at once; the playing utterance stops carrying k."""
        self.carry.pop(k, None)
        self.believe(k, v)

    def take(self, carried):
        self.carry = carried
        for k in carried:
            self._note(k)

    def finish(self):
        done, self.carry = self.carry, {}
        for k, (v, _age) in done.items():
            self.believe(k, v)

    def cut(self):
        back, self.carry = self.carry, {}
        for k in back:
            self._note(k)
        return back

    def regions_of(self, n):
        return tuple(self.at.get(n, ()))
