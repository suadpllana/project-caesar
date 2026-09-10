"""Shedding a peg.

Only the runs that carry the shed peg as one of their two youngest keepers change: a run that
merely contains it still has two younger living pegs above it, so it still stands for two keepers
or more and nothing about it has to be recomputed. That is why a shed costs the peg's two buckets
rather than a pass over the blocks.
"""
from keep import cover, live


def shed(a, p, t):
    a.t = t
    v, i = a.home.pop(p)
    cover.sink(a, v, i)
    hurt = []
    for r in a.hi_at.pop(p, ()):
        if not r[live.OK] or a.pn[r[live.V]][r[live.HI]] != p:
            continue
        w = r[live.V]
        j = cover.under(a, w, i, r[live.T1])
        if j is None:
            live.kill(a, r)
        else:
            r[live.HI] = j
            r[live.PEN] = cover.under(a, w, j, r[live.T1])
            live.file(a, r)
        hurt.append(r[live.B])
    for r in a.pen_at.pop(p, ()):
        if not r[live.OK] or r[live.PEN] is None or a.pn[r[live.V]][r[live.PEN]] != p:
            continue
        w = r[live.V]
        r[live.PEN] = cover.under(a, w, i, r[live.T1])
        if r[live.PEN] is not None:
            a.pen_at.setdefault(a.pn[w][r[live.PEN]], []).append(r)
        hurt.append(r[live.B])
    for b in sorted(set(hurt)):
        live.touch(a, b, t)
    live.flush(a)
