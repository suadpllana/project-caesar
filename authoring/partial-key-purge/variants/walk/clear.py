def wipe(store, eff):
    """New values of every row the statement clears.

    A row is cleared when it lost a setnull reference and is not itself removed; the listed
    columns of every such reference go null, and the removed set, already settled on the old
    values, is not revisited. A row counts as cleared even when those columns were null."""
    new = {}
    for t, rid, ref in eff.lost:
        if ref.act != "setnull" or (t, rid) in eff.gone:
            continue
        vals = new.get((t, rid))
        if vals is None:
            vals = new[(t, rid)] = list(store.get(t, rid))
        for col in ref.wipe:
            vals[col] = None
    return new
