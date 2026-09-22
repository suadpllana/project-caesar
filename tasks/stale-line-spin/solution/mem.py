"""Global memory and one cache per multiprocessor, for the whole launch.

The caches belong to the multiprocessors, not to the blocks: a block placed later inherits
whatever its multiprocessor fetched for the blocks before it. Nothing keeps the caches in
step with memory or with each other:

  cached load    answers from the line if it is there, otherwise copies the four words of
                 the line as memory holds them now (dropping the oldest fill when full)
  bypass load    answers from memory and drops the line from its own cache
  store          writes memory, and the storer's own copy of the word if it has the line
  atomic add     works on memory only; every cached copy, the issuer's included, stays
  fence          empties the issuer's own cache

Loads report whether they changed the cache, because a spin attempt that changes nothing is
the only kind of issue a stretch of time may be skipped over.
"""
from sim.line import Lines

LW = 4


class Mem:
    def __init__(self, init, sms, cap):
        self.gm = dict(init)
        self.l1 = [Lines(cap) for _ in range(sms)]

    def word(self, a):
        return self.gm.get(a, 0)

    def ld(self, sm, a, cached):
        """Returns (value, whether this multiprocessor's cache changed)."""
        ln = a // LW
        c = self.l1[sm]
        if cached:
            row = c.get(ln)
            if row is not None:
                return row[a % LW], False
            base = ln * LW
            gm = self.gm
            row = [gm.get(base, 0), gm.get(base + 1, 0), gm.get(base + 2, 0),
                   gm.get(base + 3, 0)]
            c.put(ln, row)
            return row[a % LW], True
        return self.gm.get(a, 0), c.drop(ln)

    def peek(self, sm, a, cached):
        """What a load would answer, and whether it would change the cache - without doing it."""
        ln = a // LW
        row = self.l1[sm].get(ln)
        if cached:
            if row is not None:
                return row[a % LW], False
            return self.gm.get(a, 0), True
        return self.gm.get(a, 0), row is not None

    def st(self, sm, a, v):
        self.gm[a] = v
        row = self.l1[sm].get(a // LW)
        if row is not None:
            row[a % LW] = v

    def add(self, sm, a, v):
        old = self.gm.get(a, 0)
        self.gm[a] = old + v
        return old

    def fence(self, sm):
        return self.l1[sm].wipe()
