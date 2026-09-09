from link import view
from reg import order


def joined(h, r):
    return None


def parted(h, r):
    return None


def moved(h, r, was):
    return None


def find(h, caller, sym):
    seen = view.keys(h, caller)
    for r in order.live(h):
        if view.den(h, r) not in seen:
            continue
        for s, _fall in r.pubs:
            if s == sym:
                return r
    return None
