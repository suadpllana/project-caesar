from reg import order


def rebuild(h):
    idx = {}
    for r in order.live(h):
        for sym, _fall in r.pubs:
            if sym not in idx:
                idx[sym] = r
    h.idx = idx


def joined(h, r):
    rebuild(h)


def parted(h, r):
    rebuild(h)


def find(h, sym):
    return getattr(h, "idx", {}).get(sym)
