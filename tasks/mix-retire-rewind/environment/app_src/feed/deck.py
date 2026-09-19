from feed import shuf


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


def at(box, j, took):
    n = len(box.lens[j])
    return took // n, took % n
