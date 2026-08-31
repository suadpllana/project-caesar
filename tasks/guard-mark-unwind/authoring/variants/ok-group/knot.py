def reap(bd, fid, t, pay):
    for p in pay:
        bd.errs.append((t, fid, p))
    return True


def wait(bd, g, left):
    return "hold"


def snag(bd, left):
    return True


def shut(bd, ch, g):
    if g is not None and g is not bd.gd:
        return ("cut", g)
    if not bd.errs:
        return None
    out = []
    for key in sorted(set((e[0], e[1]) for e in bd.errs)):
        out += [e[2] for e in bd.errs if (e[0], e[1]) == key]
    return ("bun", out)
