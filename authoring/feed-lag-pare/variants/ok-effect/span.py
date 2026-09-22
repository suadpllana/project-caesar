from lg import fold


def build(store, pins, key):
    top = pins.trailing(key)
    cuts = sorted(p for p in pins.held(key) if 0 < p <= top)
    rows = []
    floor = 0
    below = fold.ABSENT
    for edge in cuts:
        seqs = store.at(key, floor, edge)
        if seqs:
            eff = fold.NOP
            for seq in seqs:
                kind, _key, arg = store.entry(seq)
                eff = fold.join(eff, fold.make(kind, arg))
            above = fold.land(eff, below)
            rows.append((floor, edge, len(seqs), seqs[-1], below, above))
            below = above
        floor = edge
    return rows


def table(store, pins, key):
    if key in store.dirty or key not in store.tab:
        store.tab[key] = build(store, pins, key)
        store.dirty.discard(key)
    return store.tab[key]


def worth(row):
    return row[2] - (0 if fold.same(row[4], row[5]) else 1)


def board(store, pins):
    """Every worthwhile pair, bucketed by how many entries it removes."""
    bins = {}
    for key in store.keys():
        for row in table(store, pins, key):
            won = worth(row)
            if won > 0:
                bins.setdefault(won, []).append((row[1], key, row))
    for won in bins:
        bins[won].sort(key=lambda item: (item[0], item[1]))
    return bins


def collapse(store, key, row):
    floor, edge, _count, last, below, above = row
    seqs = store.at(key, floor, edge)
    keep = None if fold.same(below, above) else last
    for seq in seqs:
        if seq != keep:
            store.drop(seq)
    if keep is not None:
        if isinstance(above, fold.Gone):
            store.put(keep, "del", key, None)
        else:
            store.put(keep, "set", key, above)
    return len(seqs) - (0 if keep is None else 1)
