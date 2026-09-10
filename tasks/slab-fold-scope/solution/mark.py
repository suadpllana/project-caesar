from tab import live


def fresh(tab, buck, lo, hi, num, jr):
    sid = tab.mint()
    live.sow(tab, buck, lo, hi, num, sid, jr)
    return sid


def keep(tab, buck, i, j, reach, jr):
    b = live.hold(tab, buck)
    sid = tab.mint()
    held = 0
    for t in range(i, j):
        if b.ds[t] in reach:
            live.retag(b, t, sid, jr)
            held += b.es[t] - b.ks[t] + 1
    for d in reach:
        live.bump(b, d, -b.sn[d], jr)
    live.bump(b, sid, held, jr)
    return sid
