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


def at_local(z, val):
    hits = []
    for lo, hi, o in segs(z):
        t = val - o
        if lo is not None and t < lo:
            continue
        if hi is not None and t >= hi:
            continue
        hits.append(t)
    if hits:
        return min(hits)
    return val - off(z, val)
