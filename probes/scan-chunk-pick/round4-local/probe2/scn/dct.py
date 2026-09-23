"""What a consulted dictionary proves about the ``i`` pages of its chunk.

Every non-null value on an ``i`` page is one of the chunk's entries, so a
comparison no entry satisfies fails every row of such a page, and one every
entry satisfies passes every row of such a page that holds no null.  The
dictionary says nothing about a ``v`` page and never settles ``nn`` or ``nu``.
"""

from scn import hdr


def good(ch, kind, v):
    """How many of the chunk's entries satisfy a comparison."""
    t = hdr.test(kind, v)
    return sum(1 for e in ch.dic if t(e))


def verdict(ngood, m, u):
    """1 / -1 / 0 for an ``i`` page with u nulls, given how many of the m
    entries satisfy the comparison."""
    if ngood == 0:
        return -1
    if ngood == m and u == 0:
        return 1
    return 0


def single(ch):
    """True when the chunk has a dictionary of exactly one entry."""
    return ch.dic is not None and len(ch.dic) == 1
