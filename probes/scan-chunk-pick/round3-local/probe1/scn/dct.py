"""What the dictionary of a chunk settles for its `i` pages.

Every non-null value on an `i` page is one of the entries of its chunk.  No
entry satisfying a comparison fails every row of the page; every entry
satisfying it, with the page holding no null, passes every row.  It says
nothing about a `v` page and never settles `nn` or `nu`.
"""


def good(dic, kind, v):
    """How many entries of the dictionary satisfy the comparison."""
    t = 0
    if kind == "ge":
        for e in dic:
            if e >= v:
                t += 1
    elif kind == "le":
        for e in dic:
            if e <= v:
                t += 1
    elif kind == "eq":
        for e in dic:
            if e == v:
                t += 1
    else:
        for e in dic:
            if e != v:
                t += 1
    return t


def settle(m, good_count, u):
    """-1 fails every row of the page, 1 passes every row, 0 settles nothing."""
    if good_count == 0:
        return -1
    if good_count == m and u == 0:
        return 1
    return 0


def single(ch, pg):
    """Whether consulting the dictionary answers a projection of the page.

    That is an `i` page holding no null in a chunk whose dictionary has a
    single entry; the entry count is known without consulting it.
    """
    return pg.form == "i" and pg.nulls == 0 and ch.dic is not None and len(ch.dic) == 1
