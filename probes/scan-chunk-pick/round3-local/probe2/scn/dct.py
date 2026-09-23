"""The dictionary of a `d` chunk.

Every non-null value on an `i` page is one of the entries of its chunk, so the
dictionary settles a comparison for an `i` page: no entry satisfying it fails
every row; every entry satisfying it, with the page holding no null, passes
every row.  It says nothing about a `v` page and never settles `nn` or `nu`.
How many entries it has, and which pages are `i`, is known without it.
"""
from scn import rd


def consult(st, ch, out):
    """Consult the dictionary of a chunk; it prints only the first time in
    the file, and once consulted it is known and costs nothing."""
    seen = st.mem.dicts
    key = (ch.c, ch.j)
    if key not in seen:
        seen.add(key)
        out.rd(ch.c, ch.j)


def settle(st, ch, pg, cd):
    """For a comparison on an `i` page: True when every row passes, False
    when every row fails, None when the dictionary cannot tell."""
    memo = st.dgood
    key = (ch.c, ch.j, cd.pos)
    good = memo.get(key)
    if good is None:
        good = 0
        for e in ch.dic:
            if rd.sat(cd, e):
                good += 1
        memo[key] = good
    if good == 0:
        return False
    if good == len(ch.dic) and pg.nulls == 0:
        return True
    return None


def single(ch, pg):
    """True when consulting the dictionary would answer a projection of the
    page: an `i` page holding no null, in a chunk whose dictionary has one
    entry."""
    return pg.form == "i" and pg.nulls == 0 and ch.dic is not None and len(ch.dic) == 1
