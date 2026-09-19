from feed import shuf


def fits(box, j):
    pool = box.note.setdefault("fits", {})
    got = pool.get(j)
    if got is None:
        got = sum(1 for v in box.lens[j] if v <= box.cap)
        pool[j] = got
    return got


def hand(box, j, ep):
    pool = box.note.setdefault("hand", {})
    got = pool.get((j, ep))
    if got is None:
        order = shuf.hand(box.seed, j, ep, len(box.lens[j]))
        good = [i for i, x in enumerate(order) if box.lens[j][x] <= box.cap]
        got = (order, good)
        if len(pool) > 256:
            pool.clear()
        pool[(j, ep)] = got
    return got


def at(box, j, took):
    if not took:
        return 0, 0
    ep, r = divmod(took - 1, fits(box, j))
    cur = hand(box, j, ep)[1][r] + 1
    if cur == len(box.lens[j]):
        return ep + 1, 0
    return ep, cur


def pick(box, j, took):
    ep, r = divmod(took, fits(box, j))
    order, good = hand(box, j, ep)
    return order[good[r]]
