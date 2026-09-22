"""Where the first plan has to be given up.

A key is cut at its held points only as far as its trailing point; everything above that is
the kept region and is never touched. Each span carries what it needs to be judged without
being walked again: how many entries of the key the log holds in it, which of them is last,
and the value at its floor and at its top. Collapsing a pair removes the rest and rewrites
that last entry - the last the log still holds, which after a budgeted pare is not the last
the program wrote. Because collapsing one pair changes no other pair, the table is patched in
place rather than rebuilt, and the pairs worth taking are offered to a heap that outlives the
command.
"""

import heapq

from lg import fold


def build(store, pins, key):
    """The spans of one key, floor to trailing point, with the value at each boundary."""
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


def freshen(store, pins, key):
    """Rebuild one key's spans and offer its worthwhile pairs to the heap."""
    rows = build(store, pins, key)
    store.tab[key] = rows
    mark = store.ver.get(key, 0) + 1
    store.ver[key] = mark
    store.dirty.discard(key)
    for floor, edge, count, last, lo, hi in rows:
        won = count - (0 if fold.same(lo, hi) else 1)
        if won > 0:
            heapq.heappush(store.heap, (-won, edge, key, floor, last, lo, hi, mark))


def settle(store, pins):
    for key in list(store.dirty):
        if key in store.idx:
            freshen(store, pins, key)
        else:
            store.tab.pop(key, None)
            store.ver[key] = store.ver.get(key, 0) + 1
            store.dirty.discard(key)


def collapse(store, key, floor, edge, last, lo, hi):
    """Collapse one pair. No other pair of any key changes, so nothing is rebuilt."""
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
    rows = store.tab.get(key)
    if rows is not None:
        kept = [row for row in rows if row[0] != floor]
        if keep is not None:
            kept.append((floor, edge, 1, keep, lo, hi))
            kept.sort()
        store.tab[key] = kept
        store.dirty.discard(key)
    return len(seqs) - (0 if keep is None else 1)
