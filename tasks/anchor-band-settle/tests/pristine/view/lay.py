class Flow:
    __slots__ = ("top", "h", "end")

    def __init__(self, top, h, end):
        self.top = top
        self.h = h
        self.end = end


def size(b, h):
    n = b.own
    if not b.shut:
        for c in b.kids:
            if not c.lift:
                n += size(c, h)
    h[b] = n
    return n


def place(b, y, top, h):
    top[b] = y
    if b.shut:
        return
    y += b.own
    for c in b.kids:
        if c.lift:
            continue
        place(c, y, top, h)
        y += h[c]


def flow(v):
    top, h = {}, {}
    y = 0
    for b in v.kids:
        if b.lift:
            continue
        size(b, h)
        place(b, y, top, h)
        y += h[b]
    return Flow(top, h, y)


def span(v, fl):
    return max(0, fl.end - v.vh)
