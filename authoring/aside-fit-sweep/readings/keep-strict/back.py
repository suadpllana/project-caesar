from pool import find, side
from reg import geom, live

def drop(h, name):
    r = live.get(h, name)
    if not r.live:
        return
    r.live = False
    give(h, r.at, r.size)

def give(h, a, n):
    if n < geom.KEEP:
        side.park(h, a, n)
    else:
        find.add(h, a, n)
