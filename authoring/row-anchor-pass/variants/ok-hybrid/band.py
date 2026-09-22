"""Correct variant: the pinned group found by galloping outward rather than by bisection."""


def pinned(gm, off):
    n = gm.ngroups()
    gi = 0
    step = 1
    while gi + step < n and gm.gtop(gi + step) <= off:
        gi += step
        step *= 2
    step = max(step // 2, 1)
    while step:
        if gi + step < n and gm.gtop(gi + step) <= off:
            gi += step
        step //= 2
    return gi


def band(gm, off):
    gi = pinned(gm, off)
    nxt = gm.gtop(gi + 1) if gi + 1 < gm.ngroups() else gm.total()
    room = nxt - off
    hh = gm.ghh(gi)
    return gi, min(hh, room)
