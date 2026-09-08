from reg import order


def joined(h, r):
    return None


def parted(h, r):
    return None


def find(h, sym):
    for r in order.live(h):
        for s, _fall in r.pubs:
            if s == sym:
                return r
    return None
