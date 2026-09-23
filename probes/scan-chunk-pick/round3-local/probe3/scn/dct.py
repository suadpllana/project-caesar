"""The dictionary of a `d` chunk.

Every non-null value on an `i` page is one of the entries of its chunk, so the
dictionary can settle a comparison for an `i` page: no entry satisfying it
fails every row; every entry satisfying it, with the page holding no null,
passes every row.  It says nothing about a `v` page and never settles `nn` or
`nu`.  How many entries it has, and which pages are `i`, is known without
consulting it.  Reading an `i` page does not consult it.
"""


def consult(mem, c, j, out):
    """Consult the dictionary of chunk j of column c; prints the first time
    in the file only.  A dictionary already consulted costs nothing."""
    seen = mem.seen[c]
    if not seen[j]:
        seen[j] = 1
        out.rd(c, j)


def good(dic, kind, v):
    """How many entries satisfy a comparison (no reliance on their order)."""
    if kind == "ge":
        return sum(1 for e in dic if e >= v)
    if kind == "le":
        return sum(1 for e in dic if e <= v)
    if kind == "eq":
        return dic.count(v)
    return len(dic) - dic.count(v)


def settle(dic, kind, v, u):
    """For a comparison on an `i` page with u nulls: True when the dictionary
    proves it holds for every row, False when it proves it fails for every
    row, None when it settles nothing."""
    g = good(dic, kind, v)
    if g == 0:
        return False
    if g == len(dic) and u == 0:
        return True
    return None
