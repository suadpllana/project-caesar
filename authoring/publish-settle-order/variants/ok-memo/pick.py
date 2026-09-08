from reg import order


def joined(h, r):
    h.memo = {}


def parted(h, r):
    h.memo = {}


def find(h, sym):
    memo = getattr(h, "memo", None)
    if memo is None:
        memo = h.memo = {}
    if sym in memo:
        return memo[sym]
    got = None
    for r in order.live(h):
        if got is not None:
            break
        for s, _fall in r.pubs:
            if s == sym:
                got = r
                break
    memo[sym] = got
    return got
