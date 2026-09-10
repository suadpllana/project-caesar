from tab import live


def part(tab, buck, lo, hi, jr):
    b = live.hold(tab, buck)
    i, j = live.window(b, lo, hi)
    if i >= j:
        return 0
    fresh = []
    took = 0
    for a, z, num, sid in b.rs[i:j]:
        if a < lo:
            fresh.append([a, lo - 1, num, sid])
        if z > hi:
            fresh.append([hi + 1, z, num, sid])
        bit = min(z, hi) - max(a, lo) + 1
        live.count(b, sid, -bit, jr)
        took += bit
    live.fit(b, i, j, fresh, jr)
    live.weigh(b, -took, jr)
    return took
