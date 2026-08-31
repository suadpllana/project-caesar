def reap(bd, fid, t, pay):
    for p in pay:
        i = len(bd.errs)
        while i > 0 and (bd.errs[i - 1][0], bd.errs[i - 1][1]) > (t, fid):
            i -= 1
        bd.errs.insert(i, (t, fid, p))
    return True


def wait(bd, g, left):
    return "hold"


def snag(bd, left):
    return True


def shut(bd, ch, g):
    if g is not None and g is not bd.gd:
        return ("cut", g)
    if bd.errs:
        return ("bun", [e[2] for e in bd.errs])
    return None
