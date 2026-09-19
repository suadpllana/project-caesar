from feed import shuf


def fits(box, j):
    pool = box.note.setdefault("fits", {})
    got = pool.get(j)
    if got is None:
        got = sum(1 for v in box.lens[j] if v <= box.cap)
        pool[j] = got
    return got


def at(box, j, took):
    n = len(box.lens[j])
    lens = box.lens[j]
    cur = ep = 0
    order = shuf.hand(box.seed, j, ep, n)
    left = took
    while left > 0:
        x = order[cur]
        cur += 1
        if cur == n:
            cur = 0
            ep += 1
            order = shuf.hand(box.seed, j, ep, n)
        if lens[x] <= box.cap:
            left -= 1
    return ep, cur


def pick(box, j, took):
    n = len(box.lens[j])
    lens = box.lens[j]
    ep, cur = at(box, j, took)
    order = shuf.hand(box.seed, j, ep, n)
    while True:
        x = order[cur]
        cur += 1
        if cur == n:
            cur = 0
            ep += 1
            order = shuf.hand(box.seed, j, ep, n)
        if lens[x] <= box.cap:
            return x
