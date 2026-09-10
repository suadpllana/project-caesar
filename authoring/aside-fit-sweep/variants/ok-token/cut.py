"""Serving a request: where the bytes come from, and how many of them the caller ends up with.

The order is fixed by the rules and is not the order an allocator usually has. The aside list is
asked first, by exact size; only then the map; and only when the map cannot answer does
everything aside go back to it for one more try - which is a change to the arena that stands
whether or not that try succeeds.

A range taken from the aside list is taken whole and nothing is split, so the sliver rule does
not enter into it. A range carved out of the map does: if what would be left standing free after
it, up to the end of its part, is fewer than sixteen bytes, those bytes go to the allocation
instead. The size that comes back from here is therefore not the size that was asked for, and it
is the size the record keeps, the size the range is set aside under when it is freed, and the
size a later request has to match exactly to reuse it.
"""
from pool import find, side
from reg import geom, live, say


def want(h, name, size, out):
    r = live.get(h, name)
    if r.live:
        return
    n = geom.up(size)
    if not geom.ok(h, n):
        say.no(out, r.id)
        return
    got = grab(h, n)
    if got is None:
        say.no(out, r.id)
        return
    r.at, r.size, r.live = got[0], got[1], True
    say.at(out, r.id, got[0], got[1])


def grab(h, n):
    """n rounded bytes, from the aside list if it has them and from the map if it does not."""
    hit = side.match(h, n)
    if hit is not None:
        return hit
    a = find.spot(h, n)
    if a is None:
        side.all_back(h)
        a = find.spot(h, n)
        if a is None:
            return None
    return carve(h, a, n)


def carve(h, a, n):
    t = find.after(h, a, n)
    size = n + t if 0 < t < geom.SLIVER else n
    find.take(h, a, size)
    return a, size
