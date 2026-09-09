"""Whether a live unit has to stay, and the ledger that answers it without a scan.

The rule is a hold of its own, a live unit that needs it as a dependency, or a live unit that
brought it up as the answer to a call. The second half of a `needs` entry is what separates the
two kinds of declared edge: a hard one keeps its target up, an ordering one only decided when the
target came up. The third kind of edge is not declared at all: it is made by a resolution, it
belongs to the caller's current publication, and it goes when that publication does - which is
why it is kept on the record beside `uses` and given back in `parted`, not when the caller next
comes up.

Asking the question by walking the live set costs the live set every time, and a teardown asks
it once per candidate per pass. What makes a ledger possible instead is that the answer changes
only when a unit is published, retired, or binds a unit it brought up, and that it counts units
rather than edges - a unit that names the same dependency twice is one dependent, and a ledger
that forgets it leaves that dependency standing forever.
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


def tied(h, r, t):
    """r brought t up as the answer to a call: r keeps t as a dependency would, until r goes down."""
    r.ties.append(t.name)
    owed = _owed(h)
    owed[t.name] = owed.get(t.name, 0) + 1


def parted(h, r):
    """r has gone down. Give back what it was holding, and name whatever that frees."""
    r.ties = []
    return []


def wanted(h, r):
    return hold.held(h, r.name) > 0 or _owed(h).get(r.name, 0) > 0
