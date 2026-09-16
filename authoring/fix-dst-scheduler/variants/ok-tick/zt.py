def spans(z):
    out = []
    lo = None
    o = z.base
    for at, no in z.shifts:
        out.append((lo, at, o))
        lo = at
        o = no
    out.append((lo, None, o))
    return out


def off(z, t):
    o = z.base
    for at, no in z.shifts:
        if at <= t:
            o = no
    return o


def loc(z, t):
    return t + off(z, t)


def tod(z, t):
    return loc(z, t) % 1440


def day(z, t):
    return loc(z, t) // 1440


def edge(z, t):
    later = [at for at, _ in z.shifts if at > t]
    return min(later) if later else None


def at_local(z, val):
    rows = spans(z)
    for lo, hi, o in sorted(rows, key=lambda r: r[2]):
        t = val - o
        if (lo is None or t >= lo) and (hi is None or t < hi):
            if loc(z, t) == val:
                return t
    best = None
    for lo, hi, o in rows:
        t = val - o + 1
        if lo is not None and t < lo:
            t = lo
        if hi is not None and t >= hi:
            continue
        if best is None or t < best:
            best = t
    return best


def next_day(z, t):
    stop = day(z, t)
    at = t
    while True:
        nxt = (loc(z, at) // 1440 + 1) * 1440 - off(z, at)
        e = edge(z, at)
        if e is not None and e <= nxt:
            if day(z, e) != stop:
                return e
            at = e
            continue
        return nxt
