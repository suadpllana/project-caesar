from lg import fold


def build(store, pins, key):
    seqs = store.at(key, 0, store.head)
    top = pins.trailing(key)
    cuts = sorted(p for p in pins.held(key) if 0 < p <= top)
    out = []
    cur = fold.ABSENT
    floor = 0
    at = 0
    for edge in cuts:
        lo = cur
        count = 0
        last = None
        while at < len(seqs) and seqs[at] <= edge:
            kind, _key, arg = store.entry(seqs[at])
            cur = fold.step(cur, kind, arg)
            last = seqs[at]
            count += 1
            at += 1
        if count:
            out.append((floor, edge, count, last, lo, cur))
        floor = edge
    return out


def table(store, pins, key):
    if key in store.dirty or key not in store.tab:
        store.tab[key] = build(store, pins, key)
        store.dirty.discard(key)
    return store.tab[key]


def pairs(store, pins):
    out = []
    for key in list(store.idx):
        for floor, edge, count, last, lo, hi in table(store, pins, key):
            won = count - (0 if fold.same(lo, hi) else 1)
            if won > 0:
                out.append((-won, edge, key, floor, last, lo, hi))
    return out


def collapse(store, key, floor, edge, last, lo, hi):
    seqs = store.at(key, floor, edge)
    keep = None if fold.same(lo, hi) else last
    for seq in seqs:
        if seq != keep:
            store.drop(seq)
    if keep is not None:
        if hi is fold.ABSENT:
            store.put(keep, "del", key, None)
        else:
            store.put(keep, "set", key, hi)
    return len(seqs) - (0 if keep is None else 1)
