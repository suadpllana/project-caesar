"""Releasing a hold, and the cascade that follows it.

The rule is that the last unwanted unit in publication order goes down, that the retirement is
applied before the next candidate is chosen, and that this repeats until a pass finds nothing.
Read as written it is a scan of the live set per retirement, which a teardown of a deep forest
turns into a quadratic walk.

What replaces it is a queue of units that may have stopped being wanted, kept in reverse
publication order and consulted lazily. A unit joins it in exactly three situations: it is
published with nothing wanting it, the last live unit that needed it goes down, or the hold it
was standing on is given back. Nothing else can change the answer, so nothing else needs to be
watched, and a unit found still wanted when its turn comes is simply dropped from the queue -
whatever makes it unwanted later will put it back.

The queue is keyed by the publication key rather than by position, and that is not a
convenience. Positions shift as units are spliced out and in, a dependency that retired and came
back sits *after* the dependent that needs it, and a unit brought up by a call sits *before* the
caller that keeps it; so a cascade can expose a candidate on either side of the unit that exposed
it. The key is a tuple with no numeric negative, so the heap holds a small wrapper whose ordering
is reversed rather than a negated number.
"""
import heapq

from link import pick, want
from reg import hold, order, say, tab


class _Last:
    __slots__ = ("at", "name")

    def __init__(self, at, name):
        self.at = at
        self.name = name

    def __lt__(self, other):
        return self.at > other.at


def _queue(h):
    q = getattr(h, "loose", None)
    if q is None:
        q = h.loose = []
    return q


def note(h, r):
    heapq.heappush(_queue(h), _Last(r.at, r.name))


def let(h, name, out):
    r = tab.get(h, name)
    hold.give(h, name)
    if not r.live:
        return
    note(h, r)
    _sweep(h, out)


def _sweep(h, out):
    q = _queue(h)
    while q:
        top = heapq.heappop(q)
        go = h.units.get(top.name)
        if go is None or not go.live or go.at != top.at or want.wanted(h, go):
            continue
        for freed in want.parted(h, go):
            rec = h.units.get(freed)
            if rec is not None and rec.live:
                note(h, rec)
        go.live = False
        order.drop(h, go)
        pick.parted(h, go)
        say.down(out, go.name)
