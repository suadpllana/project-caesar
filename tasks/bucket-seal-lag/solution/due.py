"""Reference `ripe`: may this bucket be sealed now.

The requirement is that every stamp still able to reach the gather is above the
bucket's last stamp, so the question is about the whole machine and not about
the gather's own doorstep. Everything that holds anything is asked what it can
still emit, and what it can still emit is routed here; the smallest answer is
the bound. A node two hops upstream with nothing in front of it counts exactly
as much as an immediate predecessor.

Three of the accounts are easy to leave out and each of them keeps a bucket
open that a shorter reading seals:

  The gather's own inbox. Those items have arrived here and have not been put
  in a bucket yet, so they land where their stamp says and no routing is
  involved.

  The gather itself, as a node. Its open buckets emit their last stamps when
  they seal, and on a graph with a way back that emission returns here. The
  lowest open bucket is what holds the next one up.

  Every gather elsewhere, for the same reason.
"""

from flow import emit, route


def ripe(st, gn, b):
    hi = (b + 1) * st.g.par[gn] - 1
    for x in st.box[gn]:
        if x <= hi:
            return False
    for n in st.g.names:
        o = emit.own(st, n)
        if o is None:
            continue
        v = route.carry(st, n, o, gn)
        if v is not None and v <= hi:
            return False
    return True
