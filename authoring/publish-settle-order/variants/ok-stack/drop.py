import heapq

from link import pick, want
from reg import hold, order, say, tab


def _loose(h):
    q = getattr(h, "loose", None)
    if q is None:
        q = h.loose = []
    return q


def note(h, r):
    heapq.heappush(_loose(h), (-r.at, r.name))


def let(h, name, out):
    r = tab.get(h, name)
    if not r.live or hold.held(h, name) <= 0:
        return
    hold.give(h, name)
    note(h, r)
    _sweep(h, out)


def _sweep(h, out):
    q = _loose(h)
    while q:
        key, name = heapq.heappop(q)
        go = h.units[name]
        if not go.live or go.at != -key or want.wanted(h, go):
            continue
        for freed in want.parted(h, go):
            rec = h.units.get(freed)
            if rec is not None and rec.live:
                note(h, rec)
        go.live = False
        order.drop(h, go)
        pick.parted(h, go)
        say.down(out, go.name)
