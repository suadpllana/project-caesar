"""Whether a live unit has to stay, and the ledger that answers it without a scan.

The rule is a hold of its own, or a live unit that needs it as a dependency. The second half of
a `needs` entry is what separates the two kinds of edge: a hard one keeps its target up, an
ordering one only decided when the target came up.

Asking that question by walking the live set costs the live set every time, and a teardown asks
it once per candidate per pass. What makes a ledger possible instead is that the answer changes
only when a unit is published or retired, and that it counts units rather than edges - a unit
that names the same dependency twice is one dependent, and a ledger that forgets it leaves that
dependency standing forever.
"""
from reg import hold


def _owed(h):
    d = getattr(h, "owed", None)
    if d is None:
        d = h.owed = {}
    return d


def _hard(r):
    return dict.fromkeys(other for other, kind in r.needs if kind)


def joined(h, r):
    owed = _owed(h)
    for name in _hard(r):
        owed[name] = owed.get(name, 0) + 1


def parted(h, r):
    """r has gone down. Give back what it was holding, and name whatever that frees."""
    owed = _owed(h)
    return []


def wanted(h, r):
    return hold.held(h, r.name) > 0 or _owed(h).get(r.name, 0) > 0
