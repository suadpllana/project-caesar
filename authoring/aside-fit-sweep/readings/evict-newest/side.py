from pool import find
from reg import geom

def _bag(h):
    b = getattr(h, "sb", None)
    if b is None:
        b = h.sb = ({}, {}, [0])
    return b

def park(h, a, n):
    held, bysize, tick = _bag(h)
    tick[0] += 1
    held[tick[0]] = (a, n)
    bysize.setdefault(n, []).append(tick[0])
    while len(held) > geom.ROOM:
        oa, on = held.pop(next(reversed(held)))
        find.add(h, oa, on)

def match(h, n):
    held, bysize, _tick = _bag(h)
    tags = bysize.get(n)
    while tags:
        got = held.pop(tags.pop(), None)
        if got is not None:
            return got
    return None

def all_back(h):
    held, bysize, _tick = _bag(h)
    for a, n in held.values():
        find.add(h, a, n)
    held.clear()
    bysize.clear()
