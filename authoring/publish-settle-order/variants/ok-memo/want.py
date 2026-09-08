"""Whether a live unit has to stay.

A hold of its own keeps it, and so does any live unit that needs it as a dependency. The second
half of a `needs` entry is what separates the two kinds of edge: a hard one keeps its target up,
an ordering one only decided when the target came up and holds nothing afterwards. Units that
are no longer live keep nothing either, which is what lets a cascade run at all - `order.live`
is exactly the units still standing.
"""
from reg import hold, order


def wanted(h, r):
    if hold.held(h, r.name) > 0:
        return True
    for o in order.live(h):
        if o is r:
            continue
        for other, kind in o.needs:
            if kind and other == r.name:
                return True
    return False
