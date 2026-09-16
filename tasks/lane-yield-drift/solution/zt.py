def segs(z):
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
        else:
            break
    return o


def loc(z, t):
    return t + off(z, t)


def tod(z, t):
    return loc(z, t) % 1440


def day(z, t):
    return loc(z, t) // 1440


def edge(z, t):
    for at, _ in z.shifts:
        if at > t:
            return at
    return None


def at_local(z, val):
    hit = None
    for lo, hi, o in segs(z):
        t = val - o
        if lo is not None and t < lo:
            continue
        if hi is not None and t >= hi:
            continue
        if hit is None or t > hit:
            hit = t
    if hit is not None:
        return hit
    over = None
    for lo, hi, o in segs(z):
        t = val - o + 1
        if lo is not None and t < lo:
            t = lo
        if hi is not None and t >= hi:
            continue
        if over is None or t < over:
            over = t
    return over


def next_day(z, t):
    while True:
        want = (loc(z, t) // 1440 + 1) * 1440
        cand = want - off(z, t)
        e = edge(z, t)
        if e is not None and e <= cand:
            if day(z, e) != day(z, t):
                return e
            t = e
            continue
        return cand
