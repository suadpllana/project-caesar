"""Reference `own`: the earliest stamp a node can still put on its out edges.

The engine asks this of every node, and the answer is only about what the node
holds right now -- what may still arrive at it is somebody else's account, and
gets there through `route.carry` from wherever it is sitting.

The two kinds that are not "the smallest thing I am holding":

  A lift never passes anything below its floor; it lifts it. So a lift holding
  nothing but stale stamps still emits, at its own floor.

  A gather does not pass items on at all. It puts each one in a bucket and emits
  the bucket's last stamp when that bucket is sealed, so what it can still emit
  is the last stamp of the lowest bucket it has open -- and of the bucket any
  item still sitting in its inbox would land in, skipping any bucket that has
  already been sealed, because an item landing in one of those is lost and
  emits nothing at all.
"""


def own(st, n):
    g = st.g
    k = g.kind[n]
    if k == "src":
        return None if st.shut[n] else st.low[n]
    if k == "sink":
        return None
    box = st.box[n]
    if k == "relay":
        return min(box) if box else None
    if k == "lift":
        if not box:
            return None
        x = min(box)
        return x if x >= g.par[n] else g.par[n]
    if k == "gather":
        w = g.par[n]
        best = None
        for b in st.buk[n]:
            v = (b + 1) * w - 1
            if best is None or v < best:
                best = v
        for x in box:
            v = (x // w + 1) * w - 1
            if best is None or v < best:
                best = v
        return best
    return None
