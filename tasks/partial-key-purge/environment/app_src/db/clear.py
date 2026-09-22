def wipe(store, ref, tab, rid):
    for c in ref.cols:
        store.put(tab, rid, c, None)
