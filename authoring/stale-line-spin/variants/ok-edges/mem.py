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

A sum reads whole lines the same two ways. Loads report whether they changed the cache,
because an issue that changes nothing can be repeated without being stepped.

Two things the clock needs besides the loads:

  * a running sum of memory over any range of lines, so that a stretch in which a sum read
    thousands of lines straight from memory can be settled with one lookup. Memory is sparse,
    so words are kept grouped by chunks of lines, with a total per chunk and per line;
  * a hook called with the address of every write before the write lands, so that a clock
    that is carrying some multiprocessor forward without stepping it can settle that
    multiprocessor first if the write is one it would have seen.
"""
from sim.line import Lines

LW = 4
CHUNK = 1 << 12


class Mem:
    def __init__(self, init, sms, cap):
        self.gm = {}
        self.l1 = [Lines(cap) for _ in range(sms)]
        self.chunk = {}           # chunk number -> sum of every word in it
        self.lines = {}           # chunk number -> {line: sum of its words}, lines ever written
        self.before_write = None  # called with (sm, address) ahead of every write
        for a, v in init.items():
            self.put(a, v)

    def word(self, a):
        return self.gm.get(a, 0)

    def words(self, ln):
        gm, base = self.gm, ln * LW
        return [gm.get(base, 0), gm.get(base + 1, 0), gm.get(base + 2, 0), gm.get(base + 3, 0)]

    def put(self, a, v):
        d = v - self.gm.get(a, 0)
        self.gm[a] = v
        if d:
            ln = a // LW
            c = ln // CHUNK
            self.chunk[c] = self.chunk.get(c, 0) + d
            per = self.lines.get(c)
            if per is None:
                per = self.lines[c] = {}
            per[ln] = per.get(ln, 0) + d

    def span(self, lo, hi):
        """The sum of every word of lines lo .. hi-1, as memory holds them now."""
        if hi <= lo:
            return 0
        c0, c1 = lo // CHUNK, (hi - 1) // CHUNK
        total = 0
        first = self.lines.get(c0)
        if first:
            for ln, v in first.items():
                if lo <= ln < hi:
                    total += v
        if c1 == c0:
            return total
        last = self.lines.get(c1)
        if last:
            for ln, v in last.items():
                if ln < hi:
                    total += v
        chunk = self.chunk
        if c1 - c0 - 1 <= len(chunk):
            for c in range(c0 + 1, c1):
                total += chunk.get(c, 0)
        else:
            for c, v in chunk.items():
                if c0 < c < c1:
                    total += v
        return total

    def ld(self, sm, a, cached):
        """Returns (value, whether this multiprocessor's cache changed)."""
        row, changed = self.row(sm, a // LW, cached)
        return row[a % LW], changed

    def row(self, sm, ln, cached):
        """One whole line, read as a load of that kind reads it: (words, changed)."""
        c = self.l1[sm]
        if cached:
            row = c.get(ln)
            if row is not None:
                return row, False
            row = self.words(ln)
            c.put(ln, row)
            return row, True
        return self.words(ln), c.drop(ln)

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
        if self.before_write is not None:
            self.before_write(sm, a)
        self.put(a, v)
        row = self.l1[sm].get(a // LW)
        if row is not None:
            row[a % LW] = v

    def add(self, sm, a, v):
        if self.before_write is not None:
            self.before_write(sm, a)
        old = self.gm.get(a, 0)
        self.put(a, old + v)
        return old

    def fence(self, sm):
        return self.l1[sm].wipe()
