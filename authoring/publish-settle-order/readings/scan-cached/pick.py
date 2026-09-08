from reg import order


def joined(h, r):
    return None


def parted(h, r):
    return None


def find(h, sym):
    for r in order.live(h):
        got = getattr(r, "symset", None)
        if got is None:
            got = {p[0] for p in r.pubs}
            r.symset = got
        if sym in got:
            return r
    return None
