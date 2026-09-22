from lg import fold


def shown(val):
    return "-" if val is fold.ABSENT else str(val)


def report(store):
    out = ["log %d" % store.count()]
    rows = {}
    for seq, kind, key, arg in store.items():
        if kind == "del":
            item = "%dd" % seq
        else:
            item = "%d%s%d" % (seq, "s" if kind == "set" else "a", arg)
        rows.setdefault(key, []).append(item)
    for key in sorted(rows):
        out.append("k %d %s" % (key, " ".join(rows[key])))
    return out
