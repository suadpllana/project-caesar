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
    hit = side.match(h, n)
    if hit is not None:
        return hit
    a = find.spot(h, n)
    if a is None:
        return None
    return carve(h, a, n)

def carve(h, a, n):
    t = find.after(h, a, n)
    size = n + t if 0 < t < geom.SLIVER else n
    find.take(h, a, size)
    return a, size
