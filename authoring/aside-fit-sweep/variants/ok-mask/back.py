"""Giving a range back.

The threshold decides which of the two worlds the bytes land in, and everything else follows
from that: at or under 256 bytes they are set aside, where they are physically free and
otherwise inert, and over it they go into the map and join whatever they touch there. This is
the one place the two paths meet, and it is called from three of them - a `put`, the tail a
resize down leaves, and the range a resize that moved has finished with.
"""
from pool import find, side
from reg import geom, live


def drop(h, name):
    r = live.get(h, name)
    if not r.live:
        return
    r.live = False
    give(h, r.at, r.size)


def give(h, a, n):
    if n <= geom.KEEP:
        side.park(h, a, n)
    else:
        find.add(h, a, n)
