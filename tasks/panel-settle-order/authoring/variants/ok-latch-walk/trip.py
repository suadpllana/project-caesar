"""When a latch trips.

A latch reports what its entry came to rest at, so it cannot trip while the round is
still moving: a gauge that has just been computed has not necessarily settled, and a
latch that trips on it reports a value the round is about to replace. Latches are asked
once, after the round has gone quiet, and they trip for entries that moved during it,
in the order the panel declares them, at most once each per round.

Nothing trips while the panel is coming up, because the loop only asks at the end of a
round and the build is not one.
"""


def due(pl, net, ph, rno, g, moved):
    if ph != "end":
        return ()
    seen = pl.setdefault("tr", set())
    where = {}
    for i, (nm, tgt, wr) in enumerate(net.lat):
        where.setdefault(tgt, []).append((i, nm))
    hit = []
    for tgt in sorted(moved):
        for i, nm in where.get(tgt, ()):
            if (rno, nm) not in seen:
                seen.add((rno, nm))
                hit.append((i, nm))
    return tuple(nm for _i, nm in sorted(hit))


def sched(pl, net, fired):
    out = []
    for nm in fired:
        for lnm, tgt, wr in net.lat:
            if lnm == nm:
                out.extend(wr)
    return tuple(out)
