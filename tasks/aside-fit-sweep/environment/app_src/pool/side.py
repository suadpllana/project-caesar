from pool import find
from reg import geom


def _bag(h):
    b = getattr(h, "sb", None)
    if b is None:
        b = h.sb = ({}, [])
    return b


def park(h, a, n):
    bysize, seen = _bag(h)
    bysize.setdefault(n, []).append(a)
    seen.append((a, n))
    while len(seen) > geom.ROOM:
        la, ln = seen.pop()
        bysize[ln].remove(la)
        find.add(h, la, ln)


def match(h, n):
    bysize, seen = _bag(h)
    lst = bysize.get(n)
    if not lst:
        return None
    a = lst.pop(0)
    seen.remove((a, n))
    return a, n


def all_back(h):
    bysize, seen = _bag(h)
    for a, n in seen:
        find.add(h, a, n)
    bysize.clear()
    del seen[:]
