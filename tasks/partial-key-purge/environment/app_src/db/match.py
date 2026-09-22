def form(ref, vals):
    got = tuple(i for i, c in enumerate(ref.cols) if vals[c] is not None)
    if len(got) < len(ref.cols):
        return None
    return got


def ups(store, ref, vals):
    if not form(ref, vals):
        return []
    want = [vals[c] for c in ref.cols]
    kt = ref.key.tab.name
    out = []
    for pid in store.ids(kt):
        pv = store.get(kt, pid)
        if [pv[c] for c in ref.key.cols] == want:
            out.append(pid)
    return out


def downs(store, ref, pvals):
    want = [pvals[c] for c in ref.key.cols]
    ct = ref.tab.name
    out = []
    for cid in store.ids(ct):
        cv = store.get(ct, cid)
        if form(ref, cv) and [cv[c] for c in ref.cols] == want:
            out.append(cid)
    return out
