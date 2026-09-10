from tab import live


def fresh(tab, buck, lo, hi, num, jr):
    b = live.hold(tab, buck)
    sid = tab.mint()
    live.write(b, lo, hi, num, sid, jr)
    return sid


def keep(tab, buck, lo, hi, reach, jr):
    b = live.hold(tab, buck)
    sid = tab.mint()
    for start in list(live.meet(b, lo, hi)):
        end, num, was = b.run[start]
        if was in reach:
            live.erase(b, start, jr)
            live.write(b, start, end, num, sid, jr)
    return sid
