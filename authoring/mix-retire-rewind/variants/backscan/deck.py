from feed import shuf


def fits(box, j):
    pool = box.note.setdefault("fits", {})
    if j not in pool:
        pool[j] = sum(1 for v in box.lens[j] if v <= box.cap)
    return pool[j]


def hand(box, j, ep):
    pool = box.note.setdefault("hand", {})
    got = pool.get((j, ep))
    if got is None:
        got = shuf.hand(box.seed, j, ep, len(box.lens[j]))
        if len(pool) > 128:
            pool.clear()
        pool[(j, ep)] = got
    return got


def back(box, j, ep, r):
    """The r-th within-cap sample of an epoch, counted from the far end of the order."""
    lens = box.lens[j]
    order = hand(box, j, ep)
    left = fits(box, j) - r
    for i in range(len(order) - 1, -1, -1):
        if lens[order[i]] <= box.cap:
            left -= 1
            if not left:
                return i, order[i]
    raise AssertionError


def at(box, j, took):
    if not took:
        return 0, 0
    ep, r = divmod(took - 1, fits(box, j))
    place = back(box, j, ep, r)[0]
    if place + 1 == len(box.lens[j]):
        return ep + 1, 0
    return ep, place + 1


def pick(box, j, took):
    ep, r = divmod(took, fits(box, j))
    return back(box, j, ep, r)[1]
