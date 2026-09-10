"""Pegs, per volume, and the pegs a closed episode covers.

A peg is made in constant time: it records only its volume and its stamp. Which blocks it keeps is
settled afterwards, when a volume lets a block go, because a volume's hold on one block runs from
the stamp it took it to the stamp it let it go, and the pegs of that volume that keep the block are
exactly those whose stamps fall inside that run.

The skip list answers "the last living peg at or before this index" after any number of sheds, so
neither closing an episode nor shedding a peg walks a volume's peg list.
"""
import bisect


def pegged(a, p, v, t):
    a.t = t
    pt = a.pt.setdefault(v, [])
    a.pn.setdefault(v, []).append(p)
    a.pf.setdefault(v, [0]).append(len(pt) + 1)
    a.home[p] = (v, len(pt))
    pt.append(t)


def pv(a, v, i):
    """The largest living peg index of v at or before i, or None."""
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
    """Take peg index i of v out of the skip list."""
    a.pf[v][i + 1] = i


def last(a, v, t1, t2):
    """The youngest living peg of v with a stamp in [t1, t2), as an index, or None."""
    pt = a.pt.get(v)
    if not pt:
        return None
    i = pv(a, v, bisect.bisect_left(pt, t2) - 1)
    return None if i is None or pt[i] < t1 else i


def under(a, v, i, t1):
    """The living peg of v just below index i, still at or after t1, or None."""
    j = pv(a, v, i - 1)
    return None if j is None or a.pt[v][j] < t1 else j
