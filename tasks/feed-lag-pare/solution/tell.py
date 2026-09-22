"""What a program prints: a value, with absent shown as a dash, and the end report.

The report is the retained log read back key by key in ascending order, each key's entries in
sequence order and each in the form it now has.
"""

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
