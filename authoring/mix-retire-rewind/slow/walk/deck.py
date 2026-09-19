from feed import shuf


def fits(box, j):
    pool = box.note.setdefault("fits", {})
    got = pool.get(j)
    if got is None:
        got = sum(1 for v in box.lens[j] if v <= box.cap)
        pool[j] = got
    return got


def hand(box, j, ep):
    key = ("hand", j)
    got = box.note.get(key)
    if got is None or got[0] != ep:
        got = (ep, shuf.hand(box.seed, j, ep, len(box.lens[j])))
        box.note[key] = got
    return got[1]


def one(box, j, cur, ep):
    n = len(box.lens[j])
    x = hand(box, j, ep)[cur]
    cur += 1
    if cur == n:
        cur = 0
        ep += 1
    return x, cur, ep, box.lens[j][x] <= box.cap
