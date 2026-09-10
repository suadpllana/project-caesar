from tab import live


def part(tab, buck, lo, hi, jr):
    b = live.hold(tab, buck)
    i, j = live.window(b, lo, hi)
    if i >= j:
        return 0
    ks, es, ss, ds = [], [], [], []
    took = 0
    for t in range(i, j):
        a, z, s, d = b.ks[t], b.es[t], b.ss[t], b.ds[t]
        if a < lo:
            ks.append(a)
            es.append(lo - 1)
            ss.append(s)
            ds.append(d)
        if z > hi:
            ks.append(hi + 1)
            es.append(z)
            ss.append(s)
            ds.append(d)
        cut = min(z, hi) - max(a, lo) + 1
        live.bump(b, d, -cut, jr)
        took += cut
    live.splice(b, i, j, ks, es, ss, ds, jr)
    live.total(b, -took, jr)
    return took
