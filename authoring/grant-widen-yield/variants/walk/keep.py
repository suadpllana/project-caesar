"""Claims: what a transaction is still owed, and when it is allowed to try again.

A claim is not a queue entry. It carries no arrival number and it is never ordered against
one; a sweep runs oldest transaction first and, within a transaction, outermost resource
first, so a claim left a hundred lines ago and one left on this line are separated only by
whose they are and where.

Which claims a sweep tries is part of the answer rather than a speed choice, and the reason
is that a retake which ends in a refusal is not a quiet event: it walks its chain from the
store inward making younger holders give way, and only then finds the older holder that stops
it. Trying a claim that was never going to be granted therefore costs somebody their grants.
So a claim is due when it is made and again when the service moves anything at the level that
last refused it, and at no other time; `where` is that level and `watch` is the same relation
read backwards, which is what lets a line wake the handful of claims it concerns instead of
all of them.

A sweep takes the claims that are due when it starts. Everything it disturbs falls due for the
next line, including the claims its own give-ups create, so a cascade takes a line per step
rather than running to a fixed point inside one.
"""
from lk import mode, name


class Due:
    __slots__ = ("dirty", "mine", "watch", "where")

    def __init__(self):
        self.mine = {}
        self.dirty = set()
        self.watch = {}
        self.where = {}

    def owed(self, t, res):
        row = self.mine.get(t)
        return row.get(res) if row else None

    def held(self, t):
        return list(self.mine.get(t, ()))

    def park(self, cid, at):
        """Point a claim at the one level that refused it, or at nothing if untried."""
        was = self.where.pop(cid, None)
        if was is not None:
            seat = self.watch.get(was)
            if seat is not None:
                seat.discard(cid)
        if at is not None:
            self.where[cid] = at
            self.watch.setdefault(at, set()).add(cid)

    def claim(self, t, res, m, at):
        row = self.mine.setdefault(t, {})
        was = row.get(res)
        now = mode.sup(was, m)
        row[res] = now
        cid = (t, res)
        self.park(cid, at)
        if was is None or now != was:
            self.dirty.add(cid)
        else:
            self.dirty.discard(cid)

    def drop(self, t, res):
        row = self.mine.get(t)
        if not row or res not in row:
            return
        row.pop(res)
        cid = (t, res)
        self.dirty.discard(cid)
        self.park(cid, None)

    def under(self, t, res):
        row = self.mine.get(t, {})
        stem = res + "."
        return [r for r in row if r == res or r.startswith(stem)]

    def forget(self, t):
        for res in list(self.mine.get(t, ())):
            self.drop(t, res)
        self.mine.pop(t, None)

    def soak(self, book):
        """Turn the resources that moved into the claims parked on them."""
        if not book.hot:
            return
        for res in book.hot:
            for cid in self.watch.get(res, ()):
                self.dirty.add(cid)
        book.hot = set()


def settle(book, due, ages, out, take):
    """One sweep: the claims due when it starts, oldest first then outermost, tried once."""
    due.soak(book)
    if not due.dirty:
        return
    batch = sorted(due.dirty, key=lambda c: (ages[c[0]], name.depth(c[1]), name.key(c[1])))
    due.dirty = set()
    for t, res in batch:
        m = due.owed(t, res)
        if m is None:
            continue
        take(book, due, ages, t, res, m, out, False)
