def pinned(gm, off):
    gi = 0
    n = gm.ngroups()
    k = 0
    while k < n:
        if gm.gtop(k) > off:
            break
        gi = k
        k += 1
    return gi


def band(gm, off):
    gi = pinned(gm, off)
    return gi, gm.ghh(gi)
