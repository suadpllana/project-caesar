def take(gm, off):
    i = gm.at(off)
    return i, gm.key(i), gm.top(i) - off


def track(gm, held, ev, off):
    kind, gid, pos, n = ev
    if kind == "ins":
        gm.ins(gid, pos, n)
    else:
        gm.dele(gid, pos, n)
    return take(gm, off)
