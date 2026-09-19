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
        if len(pool) > 200:
            pool.clear()
        pool[(j, ep)] = got
    return got


def nth(box, j, ep, r):
    lens = box.lens[j]
    seen = -1
    for i, x in enumerate(hand(box, j, ep)):
        if lens[x] <= box.cap:
            seen += 1
            if seen == r:
                return i, x
    raise AssertionError


def at(box, j, took):
    if not took:
        return 0, 0
    ep, r = divmod(took - 1, fits(box, j))
    place = nth(box, j, ep, r)[0] + 1
    if place == len(box.lens[j]):
        return ep + 1, 0
    return ep, place


def pick(box, j, took):
    ep, r = divmod(took, fits(box, j))
    return nth(box, j, ep, r)[1]
