from db import match


def check(store, bk, eff):
    """The refusal of a planned delete, as (declaration name, row id), or None.

    A restrict reference fails on any row that lost it, removed or not. Everything else is
    judged on the end state: the remaining rows with their values after clearing. Only a row
    that lost a reference, or that matched a key row whose key was cleared, can be in a
    different position from the one it was in before, so only those are checked."""
    bad = []
    look = set()
    for t, rid, ref in eff.lost:
        if ref.act == "restrict":
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
