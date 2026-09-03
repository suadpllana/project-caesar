"""What a gauge reads, and how far from the feeds that puts it.

Two things happen here and they are the same thing seen twice.

The wiring: a gauge's expression decides what it reads as it runs, so the set that came
back from this run is the truth, and the set from the previous run is stale. Entries it
has stopped reading must stop waking it - not at the end of the round, now - or a later
move on an entry this gauge no longer reads will run it for nothing.

The distance: a gauge sits one step beyond the deepest entry it reads, so the run that
says what it reads is also the run that says where it stands. Recording that is
bookkeeping. The judgement is the other line: if any entry it turned out to read stands
at its own distance or beyond, then this gauge was reached too early, that entry has not
settled, and the value just produced is worthless. Saying so puts the gauge back, and it
runs again once the entries it waits on have taken their final values.
"""


def tie(pl, net, g, seen):
    rk = pl.setdefault("rk", {})
    old = net.dep.get(g, set())
    for d in old - seen:
        net.rdr[d].discard(g)
    for d in seen - old:
        net.rdr.setdefault(d, set()).add(g)
    net.dep[g] = set(seen)
    mine = rk.get(g, 1)
    early = [d for d in seen if net.kind[d] == "g" and rk.get(d, 1) >= mine]
    under = [rk.get(d, 1) for d in seen if net.kind[d] == "g"]
    rk[g] = (max(under) + 1) if under else 1
    return bool(early)
