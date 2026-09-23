"""What a consulted dictionary settles for the `i` pages of its chunk.

Every non-null value on an `i` page is one of the entries of its chunk.  So for
a comparison: no entry satisfying it fails every row of an `i` page; every
entry satisfying it, with the page holding no null, passes every row.  It says
nothing about a `v` page and never settles `nn` or `nu`.
"""

from scn import hdr


def good(kind, cv, dic):
    """How many entries of the dictionary satisfy a comparison."""
    t = 0
    for e in dic:
        if hdr.sat(kind, cv, e):
            t += 1
    return t


def settle(kind, cv, dic, u):
    """1: holds for every row of an `i` page with u nulls, 0: fails for every row, -1: open."""
    if kind not in hdr.CMP:
        return -1
    k = good(kind, cv, dic)
    if k == 0:
        return 0
    if k == len(dic) and u == 0:
        return 1
    return -1
