from tab import live, mark


class Again(Exception):
    pass


def part(tab, base, buck, lo, hi, jr):
    b = live.hold(tab, buck)
    i, j = live.window(b, lo, hi)
    if i >= j:
        return False
    seen = {}
    for t in range(i, j):
        d = b.ds[t]
        s = b.ss[t]
        wide = min(b.es[t], hi) - max(b.ks[t], lo) + 1
        e = seen.get(d)
        if e is None:
            seen[d] = [wide, s, s]
        else:
            e[0] += wide
            if s < e[1]:
                e[1] = s
            if s > e[2]:
                e[2] = s
    reach = set()
    for d, e in seen.items():
        if e[0] != b.sn[d]:
            continue
        if e[1] <= base < e[2]:
            raise Again()
        if e[2] <= base:
            reach.add(d)
    if len(reach) < 2:
        return False
    mark.keep(tab, buck, i, j, reach, jr)
    return True
