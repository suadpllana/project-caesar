from db import clear, hold, match


def outcome(store, tab, ids):
    idx = match.ix(store)
    gone = {(tab, i) for i in ids}
    frontier = list(gone)
    alive = {}
    lost = []
    while frontier:
        nxt = []
        for pt, p in frontier:
            pv = store.get(pt, p)
            for ref in store.tabs[pt].used:
                ct = ref.tab.name
                for c in idx.children(ref, pv):
                    key = (ct, c, ref)
                    left = alive.get(key)
                    if left is None:
                        cv = store.get(ct, c)
                        left = alive[key] = set(idx.parents(ref, match.shape(ref, cv), cv))
                    left.discard(p)
                    if not left:
                        lost.append(key)
                        if ref.act == "cascade" and (ct, c) not in gone:
                            gone.add((ct, c))
                            nxt.append((ct, c))
        frontier = nxt
    new = clear.cleared(store, gone, lost)
    return gone, new, hold.verdict(store, idx, gone, lost, new)


def delete(store, tab, ids):
    gone, new, bad = outcome(store, tab, ids)
    if bad:
        return ("refused",) + bad
    for t, i in gone:
        store.drop(t, i)
    for (t, i), vals in new.items():
        for c, v in enumerate(vals):
            store.put(t, i, c, v)
    match.stale(store)
    return ("ok", len(gone), len(new))
