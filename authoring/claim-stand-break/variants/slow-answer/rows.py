"""The committed rows, kept as a version list per key.

Nothing here is per transaction. A commit stamps its changes with the next version number and
every key keeps the whole list, because a transaction that opened long ago still has to be
answered from the rows as they stood at its base while later transactions are answered from the
rows as they stand now. `after` is the other half of that: whether a key has moved since a
given base at all, which is what a change claim is judged on.

A change is stamped whether or not it moves the value. Writing a key the value it already holds
is still a write, and that is what separates a change claim from a read claim.
"""
import bisect


class Rows:
    __slots__ = ("ver", "vs", "xs", "keys")

    def __init__(self):
        self.ver = 0
        self.vs = {}
        self.xs = {}
        self.keys = []

    def at(self, key, ver):
        """The value of key as of version ver, or None when it is not there."""
        vs = self.vs.get(key)
        if not vs:
            return None
        i = bisect.bisect_right(vs, ver)
        if not i:
            return None
        return self.xs[key][i - 1]

    def after(self, key, base):
        """Has any commit after base stamped this key."""
        vs = self.vs.get(key)
        return bool(vs) and vs[-1] > base

    def put(self, ch):
        """Take the next version number and stamp every change of a commit with it."""
        self.ver += 1
        for key in sorted(ch):
            vs = self.vs.get(key)
            if vs is None:
                self.vs[key] = [self.ver]
                self.xs[key] = [ch[key]]
                bisect.insort(self.keys, key)
            else:
                vs.append(self.ver)
                self.xs[key].append(ch[key])
        return self.ver

    def span(self, lo, hi):
        """Every key that has ever taken a version, from lo to hi, in key order."""
        keys = self.keys
        i = bisect.bisect_left(keys, lo)
        n = len(keys)
        while i < n and keys[i] <= hi:
            yield keys[i]
            i += 1

    def live(self, lo, hi):
        """The rows committed now, from lo to hi."""
        got = []
        ver = self.ver
        for key in self.span(lo, hi):
            val = self.at(key, ver)
            if val is not None:
                got.append((key, val))
        return got
