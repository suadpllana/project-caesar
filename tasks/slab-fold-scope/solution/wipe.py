from tab import live


def part(tab, buck, lo, hi):
    b = live.hold(tab, buck)
    cut = 0
    for a, (z, birth, sid) in list(live.over(b.run, lo, hi)):
        b = live.erase(b, a)
        if a < lo:
            b = live.insert(b, a, lo - 1, birth, sid)
        if z > hi:
            b = live.insert(b, hi + 1, z, birth, sid)
        cut += min(z, hi) - max(a, lo) + 1
    tab.buck[buck] = b
    return cut
