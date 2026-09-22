"""The mode lattice.

Three questions are asked of a mode and nothing else is: are two modes compatible on one
resource, what is the weakest mode that covers both, and what does a hold at this mode
require of the resource above it. The last one is the only place the task departs from the
usual table, and it departs by being derived rather than requested: a cover is IS for the
two read modes and IX for the three that can write.

`FOE` is the compatibility table read the other way round: the modes that stand in the way of
a given one. A resource at the top of the namespace is covered by every live transaction, so
asking each holder in turn whether it is compatible is quadratic in the number of open
transactions; counting holders by mode and looking at the five entries of `FOE` is not.
"""

ORD = ("IS", "IX", "S", "SIX", "X")

_OK = {
    ("IS", "IS"): True,
    ("IS", "IX"): True,
    ("IS", "S"): True,
    ("IS", "SIX"): True,
    ("IS", "X"): False,
    ("IX", "IX"): True,
    ("IX", "S"): False,
    ("IX", "SIX"): False,
    ("IX", "X"): False,
    ("S", "S"): True,
    ("S", "SIX"): False,
    ("S", "X"): False,
    ("SIX", "SIX"): False,
    ("SIX", "X"): False,
    ("X", "X"): False,
}

_SUP = {
    ("IS", "IS"): "IS",
    ("IS", "IX"): "IX",
    ("IS", "S"): "S",
    ("IS", "SIX"): "SIX",
    ("IS", "X"): "X",
    ("IX", "IX"): "IX",
    ("IX", "S"): "SIX",
    ("IX", "SIX"): "SIX",
    ("IX", "X"): "X",
    ("S", "S"): "S",
    ("S", "SIX"): "SIX",
    ("S", "X"): "X",
    ("SIX", "SIX"): "SIX",
    ("SIX", "X"): "X",
    ("X", "X"): "X",
}


def ok(a, b):
    pair = (a, b)
    return _OK[pair] if pair in _OK else _OK[(b, a)]


def sup(a, b):
    if a is None:
        return b
    if b is None:
        return a
    pair = (a, b)
    return _SUP[pair] if pair in _SUP else _SUP[(b, a)]


def cov(m):
    return "IS" if m in ("IS", "S") else "IX"


FOE = dict((a, tuple(b for b in ORD if not ok(b, a))) for a in ORD)
