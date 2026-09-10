"""Pegs per volume, and the youngest living peg a closed hold covers."""
import bisect


def pegged(a, p, v, t):
    a.t = t
    pt = a.pt.setdefault(v, [])
    a.pn.setdefault(v, []).append(p)
    a.pf.setdefault(v, [0]).append(len(pt) + 1)
    a.home[p] = (v, len(pt))
    pt.append(t)


def pv(a, v, i):
    if i < 0:
        return None
    f = a.pf[v]
    r = i + 1
    while f[r] != r:
        r = f[r]
    j = i + 1
    while f[j] != r:
        f[j], j = r, f[j]
    return r - 1 if r > 0 else None


def sink(a, v, i):
    a.pf[v][i + 1] = i


def last(a, v, t1, t2):
    pt = a.pt.get(v)
    if not pt:
        return None
    i = pv(a, v, bisect.bisect_left(pt, t2) - 1)
    return None if i is None or pt[i] < t1 else i


def under(a, v, i, t1):
    j = pv(a, v, i - 1)
    return None if j is None or a.pt[v][j] < t1 else j
