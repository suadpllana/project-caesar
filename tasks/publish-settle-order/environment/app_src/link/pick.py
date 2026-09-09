from link import view
from reg import order


def find(h, caller, sym):
    back = None
    for r in order.live(h):
        if not view.can(h, caller, r):
            continue
        for s, fall in r.pubs:
            if s != sym:
                continue
            if not fall:
                return r
            if back is None:
                back = r
    return back
