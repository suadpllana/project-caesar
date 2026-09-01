def reap(bd, fid, t, pay):
    for p in pay:
        bd.errs.append((t, fid, p))
    return True


def wait(bd, g, left):
    return "cut"


def snag(bd, left):
    return False


def shut(bd, ch, g):
    if bd.errs:
        return ("bun", [e[2] for e in sorted(bd.errs, key=lambda e: e[1])])
    if g is not None:
        return ("cut", g)
    return None
