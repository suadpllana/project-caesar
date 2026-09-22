def ver(now):
    return "v %d" % now


def fetch(lo, hi):
    return "f %d %d" % (lo, hi)


def ans(at, rows):
    if not rows:
        return "a %d -" % at
    return "a %d %s" % (at, " ".join("%d=%d" % (k, v) for k, v in rows))
