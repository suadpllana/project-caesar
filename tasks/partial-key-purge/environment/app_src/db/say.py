def verdict(res):
    if res[0] == "ok":
        return "ok %d %d" % (res[1], res[2])
    return "refused %s %d" % (res[1], res[2])


def dump(store, tab):
    out = []
    for rid in store.ids(tab):
        vals = ["-" if v is None else v for v in store.get(tab, rid)]
        out.append(" ".join([tab, str(rid)] + vals))
    return out


def audit(rows):
    out = []
    for tab, rid, gone, wiped, held in rows:
        out.append("%s %d %d %d %s" % (tab, rid, gone, wiped, "held" if held else "ok"))
    return out
