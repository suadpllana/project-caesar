import collections

from pool import find
from reg import geom

def _bag(h):
    b = getattr(h, "sb", None)
    if b is None:
        b = h.sb = ({}, collections.deque())
    return b

def park(h, a, n):
    bysize, ages = _bag(h)
    bysize.setdefault(n, []).append(a)
    ages.append((a, n))
    while sum(len(v) for v in bysize.values()) > geom.ROOM:
        oa, on = ages.popleft()
        lst = bysize.get(on)
        if not lst or oa not in lst:
            continue
        lst.remove(oa)
        find.add(h, oa, on)

def match(h, n):
    bysize, _ages = _bag(h)
    lst = bysize.get(n)
    if not lst:
        return None
    return lst.pop(), n

def all_back(h):
    bysize, ages = _bag(h)
    for n, lst in bysize.items():
        for a in lst:
            find.add(h, a, n)
    bysize.clear()
    ages.clear()
