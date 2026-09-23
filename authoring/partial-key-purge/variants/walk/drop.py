from db import clear, hold, match


class Effect:
    """What one delete statement does, worked out against the store before it runs. `gone`
    maps every removed row to the round it goes in."""

    def __init__(self):
        self.gone = {}
        self.lost = []
        self.new = {}
        self.fail = None


def plan(store, tab, ids):
    """Removed set, rounds, lost references, clearing and refusal of `delete tab ids`.

    Every (row, reference) pair keeps a count of the key rows it matched before the statement
    that are still standing. The named rows go in round 0. Removals are counted down one round
    at a time: a pair that reaches zero has lost its reference, and a pair on a cascade
    reference removes its row in the next round unless an earlier pair already did. A row
    therefore goes one round after the last row it matched through the first of its cascade
    references to run out, and never before every row it matched through it has gone, which
    is the smallest set closed under the rule: rows that match only one another never reach
    zero, and neither does a row that matches itself."""
    bk = match.book(store)
    eff = Effect()
    gone = eff.gone
    todo = []
    for rid in ids:
        gone[(tab, rid)] = 0
        todo.append((tab, rid))
    left = {}
    tabs = store.tabs
    step = 0
    while todo:
        step += 1
        nxt = []
        for pt, p in todo:
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
                            gone[(ct, c)] = step
                            nxt.append((ct, c))
        todo = nxt
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
