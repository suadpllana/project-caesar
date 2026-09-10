from pool import back, cut, find, side
from reg import geom, live, say

def resize(h, name, size, out):
    r = live.get(h, name)
    if not r.live:
        return
    n = geom.up(size)
    if not geom.ok(h, n):
        say.no(out, r.id)
        return
    a, m = r.at, r.size
    if n <= m:
        if m - n < geom.SLIVER:
            say.same(out, r.id, m)
            return
        r.size = n
        back.give(h, a + n, m - n)
        say.same(out, r.id, n)
        return
    if a + n <= geom.part_end(h, a) and side.at_edge(h, a + m, n - m):
        r.size = n
        say.same(out, r.id, n)
        return
    if a + n <= geom.part_end(h, a) and find.have(h, a + m, n - m):
        t = find.after(h, a, n)
        grown = n + t if 0 < t < geom.SLIVER else n
        find.take(h, a + m, grown - m)
        r.size = grown
        say.same(out, r.id, grown)
        return
    got = cut.grab(h, n)
    if got is None:
        say.no(out, r.id)
        return
    back.give(h, a, m)
    r.at, r.size = got[0], got[1]
    say.at(out, r.id, got[0], got[1])
