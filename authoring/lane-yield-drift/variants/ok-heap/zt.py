import bisect


def table(z):
    got = getattr(z, "_tab", None)
    if got is None or got[0] != len(z.shifts):
        starts = [-(1 << 40)] + [at for at, _ in z.shifts]
        offs = [z.base] + [o for _, o in z.shifts]
        got = (len(z.shifts), starts, offs)
        z._tab = got
    return got[1], got[2]


def off(z, t):
    starts, offs = table(z)
    return offs[bisect.bisect_right(starts, t) - 1]


def loc(z, t):
    return t + off(z, t)


def tod(z, t):
    return loc(z, t) % 1440


def day(z, t):
    return loc(z, t) // 1440


def edge(z, t):
    starts, _ = table(z)
    i = bisect.bisect_right(starts, t)
    return starts[i] if i < len(starts) else None


def at_local(z, val):
    starts, offs = table(z)
    exact = []
    past = []
    for i, o in enumerate(offs):
        lo = starts[i]
        hi = starts[i + 1] if i + 1 < len(starts) else None
        t = val - o
        if t >= lo and (hi is None or t < hi):
            exact.append(t)
        t2 = max(val - o + 1, lo)
        if hi is None or t2 < hi:
            past.append(t2)
    return max(exact) if exact else min(past)


def next_day(z, t):
    here = day(z, t)
    probe = t
    while True:
        cand = (loc(z, probe) // 1440 + 1) * 1440 - off(z, probe)
        e = edge(z, probe)
        if e is not None and e <= cand:
            if day(z, e) != here:
                return e
            probe = e
            continue
        return cand
