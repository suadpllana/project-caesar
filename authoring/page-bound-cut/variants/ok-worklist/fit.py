HEAD = 8
ENT = 2
KID = 2

TALLY = {}


def wipe(pid):
    TALLY.pop(pid, None)


def lead(a, b):
    n = len(a) if len(a) < len(b) else len(b)
    i = 0
    while i < n and a[i] == b[i]:
        i += 1
    return i


def roll(tr, pid):
    """Entry count and total entry length, kept beside the page and dropped when it moves."""
    got = TALLY.get(pid)
    page = tr.at(pid)
    ents = page.keys if page.leaf else page.seps
    if got is None or got[0] != len(ents):
        total = 0
        for e in ents:
            total += len(e)
        got = TALLY[pid] = (len(ents), total)
    return ents, got[0], got[1]


def frame(first, last, count, total, kids):
    n = HEAD + kids * KID
    if count:
        pre = lead(first, last)
        n += pre + count * ENT + total - count * pre
    return n


def bulk(tr, pid):
    page = tr.at(pid)
    ents, count, total = roll(tr, pid)
    kids = 0 if page.leaf else len(page.kids)
    if not count:
        return HEAD + kids * KID
    return frame(ents[0], ents[-1], count, total, kids)


def over(tr, pid):
    return bulk(tr, pid) > tr.cap


def under(tr, pid):
    return bulk(tr, pid) < tr.floor
