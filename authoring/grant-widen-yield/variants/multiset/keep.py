"""Second correct implementation of the claims, written to the same contract.

A claim is one record carrying its own mode and the level it is parked on, rather than the
reference's two indexes; the sweep is built from a list and sorted in place; the backward
index is a dict of lists compacted lazily when it is read.

None of that is graded. Which claims a sweep tries, and in what order, is.
"""
from lk import mode, name


class Due:
    __slots__ = ("dirty", "rec", "watch")

    def __init__(self):
        self.rec = {}
        self.watch = {}
        self.dirty = set()

    def owed(self, t, res):
        got = self.rec.get((t, res))
        return got[0] if got else None

    def held(self, t):
        return [res for (u, res) in self.rec if u == t]

    def park(self, cid, at):
        got = self.rec.get(cid)
        if got is not None and got[1] is not None:
            seat = self.watch.get(got[1])
            if seat is not None:
                seat.discard(cid)
        if got is not None:
            got[1] = at
        if at is not None:
            self.watch.setdefault(at, set()).add(cid)

    def claim(self, t, res, m, at):
        cid = (t, res)
        got = self.rec.get(cid)
        if got is None:
            self.rec[cid] = [m, None]
            self.park(cid, at)
            self.dirty.add(cid)
            return
        was = got[0]
        got[0] = mode.sup(was, m)
        self.park(cid, at)
        if got[0] != was:
            self.dirty.add(cid)
        else:
            self.dirty.discard(cid)

    def drop(self, t, res):
        cid = (t, res)
        if cid not in self.rec:
            return
        self.park(cid, None)
        del self.rec[cid]
        self.dirty.discard(cid)

    def under(self, t, res):
        stem = res + "."
        return [r for (u, r) in self.rec if u == t and (r == res or r.startswith(stem))]

    def forget(self, t):
        for res in self.held(t):
            self.drop(t, res)

    def soak(self, book):
        if not book.hot:
            return
        for res in book.hot:
            seat = self.watch.get(res)
            if seat:
                self.dirty.update(seat)
        book.hot = set()


def settle(book, due, ages, out, take):
    due.soak(book)
    if not due.dirty:
        return
    batch = list(due.dirty)
    batch.sort(key=lambda c: (ages[c[0]], name.depth(c[1]), name.key(c[1])))
    due.dirty = set()
    for cid in batch:
        got = due.rec.get(cid)
        if got is None:
            continue
        take(book, due, ages, cid[0], cid[1], got[0], out, False)
