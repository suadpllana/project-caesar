from lg import fold


def table(store, pins, key):
    seqs = store.at(key, 0, store.head)
    cuts = sorted(p for p in pins.held(key) if 0 < p <= store.head)
    out = []
    floor = 0
    at = 0
    for edge in cuts:
        count = 0
        first = None
        while at < len(seqs) and seqs[at] <= edge:
            if first is None:
                first = seqs[at]
            count += 1
            at += 1
        if count:
            out.append((floor, edge, count, first))
        floor = edge
    return out


def pairs(store, pins):
    out = []
    for key in store.keys():
        for floor, edge, count, first in table(store, pins, key):
            if count > 1:
                out.append((key, floor, edge, count, first))
    return out


def collapse(store, pins, key, floor, edge, first):
    seqs = store.at(key, floor, edge)
    hi = fold.value(store, key, edge)
    for seq in seqs:
        if seq != first:
            store.drop(seq)
    store.put(first, "set", key, 0 if hi is fold.ABSENT else hi)
    return len(seqs) - 1
