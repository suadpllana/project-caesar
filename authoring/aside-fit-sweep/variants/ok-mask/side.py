"""The ranges that have been set aside: two orders over one collection.

A freed range of 256 bytes or less does not go back to the map. It is set aside whole, and while
it is aside it belongs to nobody: it joins no neighbour, no allocation is placed in it, and no
range grows into it. What it is good for is a request of exactly its own size, which takes the
one set aside most recently. What ends it is population: over thirty-two aside, the one set
aside earliest goes back to the map and joins its neighbours there.

So one collection carries an order by age for the eviction and an order by size for the reuse,
and the reuse takes entries out of the middle of the age order. That is what the tag is for. A
range at one address and size can be set aside, taken, and set aside again, so an entry cannot
be named by what it is - only by which time it was set aside. Tags are minted in order, the
dictionary of live entries keeps them in that order, and the per-size stacks may hold tags of
entries that have already gone, which is harmless because a tag is never reused.
"""
from pool import find
from reg import geom


def _bag(h):
    b = getattr(h, "sb", None)
    if b is None:
        b = h.sb = ({}, {}, [0])
    return b


def park(h, a, n):
    """Set a range aside, and give back the oldest while more than thirty-two are aside."""
    held, bysize, tick = _bag(h)
    tick[0] += 1
    held[tick[0]] = (a, n)
    bysize.setdefault(n, []).append(tick[0])
    while len(held) > geom.ROOM:
        oa, on = held.pop(next(iter(held)))
        find.add(h, oa, on)


def match(h, n):
    """The range of exactly this size set aside most recently, if there is one."""
    held, bysize, _tick = _bag(h)
    tags = bysize.get(n)
    while tags:
        got = held.pop(tags.pop(), None)
        if got is not None:
            return got
    return None


def all_back(h):
    """Everything aside goes back to the map: what `sweep` does, and what a failed search does."""
    held, bysize, _tick = _bag(h)
    for a, n in held.values():
        find.add(h, a, n)
    held.clear()
    bysize.clear()
