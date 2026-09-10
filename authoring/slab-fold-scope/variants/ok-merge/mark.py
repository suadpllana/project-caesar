from tab import live


def fresh(tab, buck, lo, hi, num, jr):
    b = live.hold(tab, buck)
    sid = tab.mint()
    i, j = live.window(b, lo, hi)
    live.fit(b, i, j, [[lo, hi, num, sid]], jr)
    live.count(b, sid, hi - lo + 1, jr)
    live.weigh(b, hi - lo + 1, jr)
    return sid


def keep(tab, buck, lo, hi, reach, jr):
    b = live.hold(tab, buck)
    sid = tab.mint()
    i, j = live.window(b, lo, hi)
    held = 0
    made = []
    for a, z, num, was in b.rs[i:j]:
        if was in reach:
            made.append([a, z, num, sid])
            held += z - a + 1
        else:
            made.append([a, z, num, was])
    joined = []
    for one in made:
        if joined and joined[-1][1] + 1 == one[0] and joined[-1][2:] == one[2:]:
            joined[-1][1] = one[1]
        else:
            joined.append(one)
    live.fit(b, i, j, joined, jr)
    for was in reach:
        live.count(b, was, -b.own[was], jr)
    live.count(b, sid, held, jr)
    return sid
