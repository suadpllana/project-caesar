from db import clear, hold, match


class Effect:
    """What one delete statement does, worked out against the store before it runs."""

    def __init__(self):
        self.gone = set()
        self.lost = []
        self.new = {}
        self.fail = None


def plan(store, tab, ids):
    """Removed set, lost references, clearing and refusal of `delete tab ids`.

    Every (row, reference) pair keeps a count of the key rows it matched before the statement
    that are still standing. A removed row counts down each pair that matched it; a pair that
    reaches zero has lost its reference, and a pair on a cascade reference removes its row,
    which then counts down its own referrers. A row therefore goes only after every row it
    matched has gone, which is the smallest set closed under the rule: rows that match only
    one another never reach zero, and neither does a row that matches itself."""
    bk = match.book(store)
    eff = Effect()
    gone = eff.gone
    todo = []
    for rid in ids:
        gone.add((tab, rid))
        todo.append((tab, rid))
    left = {}
    tabs = store.tabs
    while todo:
        pt, p = todo.pop()
        pv = store.get(pt, p)
        for ref in tabs[pt].used:
            ct = ref.tab.name
            for c in bk.downs(ref, pv):
                slot = (ct, c, ref)
                n = left.get(slot)
                if n is None:
                    n = len(bk.ups(ref, store.get(ct, c)))
                n -= 1
                left[slot] = n
                if n == 0:
                    eff.lost.append(slot)
                    if ref.act == "cascade" and (ct, c) not in gone:
                        gone.add((ct, c))
                        todo.append((ct, c))
    eff.new = clear.wipe(store, eff)
    eff.fail = hold.check(store, bk, eff)
    return eff


def delete(store, tab, ids):
    eff = plan(store, tab, ids)
    if eff.fail is not None:
        return ("refused", eff.fail[0], eff.fail[1])
    for t, rid in eff.gone:
        store.drop(t, rid)
    for (t, rid), vals in eff.new.items():
        old = store.get(t, rid)
        for col, val in enumerate(vals):
            if old[col] != val:
                store.put(t, rid, col, val)
    match.spoil(store)
    return ("ok", len(eff.gone), len(eff.new))
