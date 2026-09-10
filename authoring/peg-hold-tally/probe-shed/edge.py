"""Shedding a peg by walking every run there is - correct, and the obvious way to write it."""
from keep import cover, live


def shed(a, p, t):
    a.t = t
    v, i = a.home.pop(p)
    cover.sink(a, v, i)
    hurt = []
    for r in a.all:
        if not r[live.OK]:
            continue
        w = r[live.V]
        j = cover.last(a, w, r[live.T1], r[live.T2])
        if j is None:
            live.kill(a, r)
            hurt.append(r[live.B])
        elif j != r[live.HI]:
            r[live.HI] = j
            a.hi_at.setdefault(a.pn[w][j], []).append(r)
    for b in sorted(set(hurt)):
        live.touch(a, b, t)
    live.flush(a)
