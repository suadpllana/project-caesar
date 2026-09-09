def add(h, r):
    h.seq[r.name] = r


def drop(h, r):
    h.seq.pop(r.name, None)


def live(h):
    return list(h.seq.values())


def pos(h, r):
    for n, x in enumerate(h.seq.values()):
        if x is r:
            return n
    return -1
