from pool import back, cut, find
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
    if find.have(h, a + m, n - m):
        grown = n + find.after(h, a, n)
        find.take(h, a + m, grown - m)
        r.size = grown
        say.same(out, r.id, grown)
        return
    back.give(h, a, m)
    got = cut.grab(h, n)
    if got is None:
        again = cut.grab(h, m)
        if again is not None:
            r.at, r.size = again[0], again[1]
        say.no(out, r.id)
        return
    r.at, r.size = got[0], got[1]
    say.at(out, r.id, got[0], got[1])
