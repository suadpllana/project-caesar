import copy

from db import clear, hold, match


def delete(store, tab, ids):
    keep = copy.deepcopy(store.data)
    log = {"gone": [], "wiped": set(), "bad": []}
    for rid in ids:
        if store.has(tab, rid):
            cut(store, tab, rid, log)
    bad = hold.check(store, log)
    if bad:
        store.data = keep
        return ("refused",) + bad
    return ("ok", len(log["gone"]), len(log["wiped"]))


def cut(store, tab, rid, log):
    vals = store.get(tab, rid)
    store.drop(tab, rid)
    log["gone"].append((tab, rid))
    for ref in store.tabs[tab].used:
        ct = ref.tab.name
        for c in match.downs(store, ref, vals):
            if not store.has(ct, c) or match.ups(store, ref, store.get(ct, c)):
                continue
            if ref.act == "cascade":
                cut(store, ct, c, log)
            elif ref.act == "setnull":
                clear.wipe(store, ref, ct, c)
                log["wiped"].add((ct, c))
            else:
                log["bad"].append((ref.name, c))
