def cleared(store, gone, lost):
    out = {}
    for tab, rid, ref in lost:
        if ref.act == "setnull" and (tab, rid) not in gone:
            row = out.setdefault((tab, rid), list(store.get(tab, rid)))
            for c in ref.wipe:
                row[c] = None
    return out
