"""Shedding a peg: only the runs whose youngest living peg it was can change."""
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
            hurt.append(r[live.B])
        else:
            r[live.HI] = j
            a.hi_at.setdefault(a.pn[w][j], []).append(r)
    for b in sorted(set(hurt)):
        live.touch(a, b, t)
    live.flush(a)
