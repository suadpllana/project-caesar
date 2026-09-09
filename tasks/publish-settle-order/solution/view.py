"""Which publications a caller is allowed to reach.

A publication is either public or private to the scope that brought it up, and a caller reads
the public ones plus, if it is private itself, the ones in its own scope. Nothing else about a
scope matters: it holds nothing up, it is not a unit, and it never appears in the trace.

`keys` is the whole of the model as far as resolution is concerned. It gives the buckets a
caller may read, and it is what lets `pick.py` answer a call without walking past publications
the caller cannot see.
"""


def _dens(h):
    d = getattr(h, "dens", None)
    if d is None:
        d = h.dens = {}
    return d


def fresh(h):
    h.scopes = getattr(h, "scopes", 0) + 1
    return h.scopes


def seal(h, r, den):
    _dens(h)[r.name] = den


def open_up(h, r):
    _dens(h)[r.name] = None


def den(h, r):
    return _dens(h).get(r.name)


def keys(h, caller):
    mine = den(h, caller)
    return (None,) if mine is None else (None, mine)
