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

The queue is keyed by the publication serial rather than by position, and that is not a
convenience. Positions shift as units are spliced out, and a dependency that retired and came
back sits *after* the dependent that needs it, so a cascade can expose a candidate later in the
order than the unit that exposed it. A structure that assumes candidates only ever appear
earlier is right on every ordinary teardown and wrong there.
"""
import heapq

from link import pick, want
from reg import hold, order, say, tab


def _queue(h):
    q = getattr(h, "loose", None)
    if q is None:
        q = h.loose = []
    return q


def note(h, r):
    heapq.heappush(_queue(h), (-r.at, r.at, r.name))


def let(h, name, out):
    r = tab.get(h, name)
    if not r.live or hold.held(h, name) <= 0:
        return
    hold.give(h, name)
    note(h, r)
    _sweep(h, out)


def _sweep(h, out):
    q = _queue(h)
    while q:
        _key, at, name = heapq.heappop(q)
        go = h.units.get(name)
        if go is None or not go.live or go.at != at or want.wanted(h, go):
            continue
        want.parted(h, go)
        go.live = False
        order.drop(h, go)
        pick.parted(h, go)
        say.down(out, go.name)
