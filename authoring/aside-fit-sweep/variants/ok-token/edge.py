"""Resizing a range that is already up.

Down is a release of the tail, through the ordinary free path, which means a tail at or under
the threshold is set aside rather than joined to whatever follows it - and a tail of fewer than
sixteen bytes is not released at all, which is the sliver rule read from the other end.

Up is the rule with the sharpest consequence. The bytes that follow are usable only when they
are in the map and only while the whole grown range stays inside one part, so a neighbour freed
one operation earlier is not usable at all: it is aside, and aside is invisible here. When the
growth cannot be had, a new range is placed first and the old one is freed afterwards, in that
order, because freeing first would set the old range aside at exactly its own size where the
request that is about to be served would match it.
"""
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
