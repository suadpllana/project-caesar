def add(h, r):
    put(h, r, None)


def put(h, r, before):
    r.fore = before
    r.back = h.tail if before is None else before.back
    if r.back is None:
        h.head = r
    else:
        r.back.fore = r
    if before is None:
        h.tail = r
    else:
        before.back = r


def drop(h, r):
    if r.back is None and h.head is not r:
        return
    if r.back is None:
        h.head = r.fore
    else:
        r.back.fore = r.fore
    if r.fore is None:
        h.tail = r.back
    else:
        r.fore.back = r.back
    r.back = None
    r.fore = None


def live(h):
    out = []
    r = h.head
    while r is not None:
        out.append(r)
        r = r.fore
    return out


def pos(h, r):
    n = 0
    x = h.head
    while x is not None:
        if x is r:
            return n
        n += 1
        x = x.fore
    return -1
