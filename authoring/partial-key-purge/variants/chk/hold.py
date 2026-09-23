from db import match

DEEPEST = 15


def verdict(store, idx, gone, lost, new):
    fails = {}

    def fail(decl, rid):
        if decl.pos not in fails or rid < fails[decl.pos][1]:
            fails[decl.pos] = (decl.name, rid)

    suspects = {}
    for tab, rid, ref in lost:
        if ref.act == "restrict":
            fail(ref, rid)
        if ref.act == "cascade" and gone.get((tab, rid), 0) > DEEPEST:
            fail(ref, rid)
        if (tab, rid) not in gone:
            suspects[(tab, rid)] = True
    shifted = {}
    for (tab, rid), vals in new.items():
        old = store.get(tab, rid)
        for key in store.tabs[tab].keys:
            if [vals[c] for c in key.cols] != [old[c] for c in key.cols]:
                shifted[(tab, rid)] = vals
                for ref in store.tabs[tab].used:
                    if ref.key is key:
                        for c in idx.children(ref, old):
                            if (ref.tab.name, c) not in gone:
                                suspects[(ref.tab.name, c)] = True
    for tab, rid in suspects:
        vals = new[(tab, rid)] if (tab, rid) in new else store.get(tab, rid)
        for ref in store.tabs[tab].refs:
            pat = match.shape(ref, vals)
            if pat is None:
                continue
            ok = pat is not False and any(
                (ref.key.tab.name, p) not in gone and not (
                    (ref.key.tab.name, p) in shifted and
                    any(shifted[(ref.key.tab.name, p)][ref.key.cols[i]] is None for i in pat))
                for p in idx.parents(ref, pat, vals))
            if not ok:
                fail(ref, rid)
        for key in store.tabs[tab].keys:
            if any(vals[c] is None for c in key.cols):
                fail(key, rid)
    if not fails:
        return None
    return fails[min(fails)]
