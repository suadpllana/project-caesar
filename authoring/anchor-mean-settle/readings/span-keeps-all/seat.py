"""The row the view is held against, and where the scroll position lands.

An anchor is a row and the distance from the view's top edge to its own top edge, which is
zero or negative. It is taken from wherever the view is now, and once taken that distance
is held: re-seating puts the scroll position back where the anchor sits at that distance,
clamped to the scroll range. The clamp is the reason the distance is held rather than
re-derived - at either end of the range part of the correction has nowhere to go, and what
is lost there is lost rather than folded back into the anchor.
"""
from pan import grid


def clip(p, x):
    lim = grid.edge(p)
    if x < 0:
        return 0
    return lim if x > lim else x


def take(p):
    r, acc = grid.hit(p)
    if r is None:
        p.anc = None
        p.dy = 0
        return
    p.anc = r
    p.dy = acc - p.top


def hold(p):
    if p.anc is None:
        p.top = clip(p, p.top)
    else:
        p.top = clip(p, grid.off(p, p.anc) - p.dy)


def roll(p, d):
    p.top = clip(p, p.top + d)
    take(p)
