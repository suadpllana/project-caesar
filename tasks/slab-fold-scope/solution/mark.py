from tab import live


def fresh(tab, buck, lo, hi, num):
    sid = tab.mint()
    tab.buck[buck] = live.insert(live.hold(tab, buck), lo, hi, num, sid)
    return sid


def keep(tab, buck, sids):
    b = live.hold(tab, buck)
    sid = tab.mint()
    for old in sids:
        for a, (z, birth, _) in list(live.items(live.get(b.own, old))):
            b = live.erase(b, a)
            b = live.insert(b, a, z, birth, sid)
    tab.buck[buck] = b
    return sid
