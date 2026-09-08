from reg import order


def find(h, sym):
    back = None
    for r in order.live(h):
        for s, fall in r.pubs:
            if s != sym:
                continue
            if not fall:
                return r
            if back is None:
                back = r
    return back
