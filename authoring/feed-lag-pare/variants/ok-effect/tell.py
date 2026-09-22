from lg import fold


def shown(val):
    return "-" if isinstance(val, fold.Gone) else str(val)


def report(store):
    out = ["log %d" % store.count()]
    seen = {}
    for seq, kind, key, arg in store.items():
        if kind == "del":
            seen.setdefault(key, []).append("%dd" % seq)
        else:
            seen.setdefault(key, []).append(
                "%d%s%d" % (seq, "s" if kind == "set" else "a", arg))
    for key in sorted(seen):
        out.append("k %d %s" % (key, " ".join(seen[key])))
    return out
