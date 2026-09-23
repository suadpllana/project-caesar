#!/bin/bash
# wrong reading restrict-only-by-losing: the reference with this reading's files
set -euo pipefail

cat > /app/db/match.py <<'PYEOF'
def form(ref, vals):
    """How a row's values stand against a reference: None when the reference is inert for
    them, False when it is broken (full, some columns null but not all), and otherwise the
    positions within the reference's columns that carry a value, which are the positions a
    matched key row has to agree on."""
    got = tuple(i for i, c in enumerate(ref.cols) if vals[c] is not None)
    if not got:
        return None
    if len(got) < len(ref.cols):
        if ref.mode == "simple":
            return None
        if ref.mode == "full":
            return False
    return got


class Book:
    """Value indexes over the store as it stands. A partial reference can leave any subset
    of its columns null, so rows are indexed once per pattern of non-null positions: key
    rows by the projection of their key onto the pattern, referencing rows by the projection
    of their own values. Built lazily and thrown away whenever the store changes."""

    def __init__(self, store):
        self.store = store
        self.up = {}
        self.down = {}

    def ups(self, ref, vals, pat=None):
        """Ids of the key rows that `vals` matches through `ref`."""
        if pat is None:
            pat = form(ref, vals)
            if not pat:
                return ()
        slot = (ref.key.name, pat)
        idx = self.up.get(slot)
        if idx is None:
            idx = {}
            kc = [ref.key.cols[i] for i in pat]
            data = self.store.data[ref.key.tab.name]
            for pid, pv in data.items():
                idx.setdefault(tuple(pv[c] for c in kc), []).append(pid)
            self.up[slot] = idx
        return idx.get(tuple(vals[ref.cols[i]] for i in pat), ())

    def downs(self, ref, pvals):
        """Ids of the rows that match, through `ref`, a key row holding `pvals`."""
        idx = self.down.get(ref.name)
        if idx is None:
            idx = {}
            data = self.store.data[ref.tab.name]
            for cid, cv in data.items():
                pat = form(ref, cv)
                if pat:
                    idx.setdefault(pat, {}).setdefault(
                        tuple(cv[ref.cols[i]] for i in pat), []).append(cid)
            self.down[ref.name] = idx
        out = []
        for pat, table in idx.items():
            hit = table.get(tuple(pvals[ref.key.cols[i]] for i in pat))
            if hit:
                out.extend(hit)
        return out


def book(store):
    got = getattr(store, "book", None)
    if got is None:
        got = store.book = Book(store)
    return got


def spoil(store):
    store.book = None
PYEOF

cat > /app/db/drop.py <<'PYEOF'
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
PYEOF

cat > /app/db/clear.py <<'PYEOF'
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
PYEOF

cat > /app/db/hold.py <<'PYEOF'
from db import match

LIMIT = 15


def check(store, bk, eff):
    """The refusal of a planned delete, as (declaration name, row id), or None.

    A restrict reference fails on any row that lost it, removed or not, and a row removed
    deeper than the limit fails every cascade reference it lost. Everything else is judged on
    the end state: the remaining rows with their values after clearing. Only a row that lost a
    reference, or that matched a key row whose key was cleared, can be in a different position
    from the one it was in before, so only those are checked."""
    bad = []
    look = set()
    for t, rid, ref in eff.lost:
        if ref.act == "restrict":
            bad.append((ref.pos, rid))
        if ref.act == "cascade" and eff.gone.get((t, rid), 0) > LIMIT:
            bad.append((ref.pos, rid))
        if (t, rid) not in eff.gone:
            look.add((t, rid))
    moved = {}
    for (t, rid), vals in eff.new.items():
        old = store.get(t, rid)
        for key in store.tabs[t].keys:
            if any(vals[c] != old[c] for c in key.cols):
                moved[(t, rid)] = vals
                for ref in store.tabs[t].used:
                    if ref.key is key:
                        for c in bk.downs(ref, old):
                            if (ref.tab.name, c) not in eff.gone:
                                look.add((ref.tab.name, c))
    for t, rid in look:
        vals = eff.new.get((t, rid)) or store.get(t, rid)
        tab = store.tabs[t]
        for ref in tab.refs:
            if ref.act == "restrict":
                continue
            pat = match.form(ref, vals)
            if pat is None:
                continue
            if pat is False or not standing(bk, eff, moved, ref, pat, vals):
                bad.append((ref.pos, rid))
        for key in tab.keys:
            if any(vals[c] is None for c in key.cols):
                bad.append((key.pos, rid))
    if not bad:
        return None
    pos = min(p for p, _ in bad)
    return (store.script.decls[pos].name, min(rid for p, rid in bad if p == pos))


def standing(bk, eff, moved, ref, pat, vals):
    """Whether some key row still matches `vals` once the statement is done."""
    kt = ref.key.tab.name
    for p in bk.ups(ref, vals, pat):
        if (kt, p) in eff.gone:
            continue
        pv = moved.get((kt, p))
        if pv is not None and any(pv[ref.key.cols[i]] is None for i in pat):
            continue
        return True
    return False
PYEOF

cat > /app/db/audit.py <<'PYEOF'
from db import drop


def audit(store):
    out = []
    for tab in store.script.tabs:
        for rid in store.ids(tab.name):
            eff = drop.plan(store, tab.name, [rid])
            out.append((tab.name, rid, len(eff.gone), len(eff.new), eff.fail))
    return out
PYEOF
