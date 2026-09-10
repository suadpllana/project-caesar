from tab import live


def fresh(tab, buck, lo, hi, num, jr):
    sid = tab.mint()
    b = live.hold(tab, buck)
    for key in range(lo, hi + 1):
        live.give(b, key, sid, num, jr)
    return sid


def keep(tab, buck, reach, jr):
    b = live.hold(tab, buck)
    sid = tab.mint()
    for key, got in list(b.own.items()):
        if got[0] in reach:
            live.drop(b, key, jr)
            live.give(b, key, sid, got[1], jr)
    return sid
