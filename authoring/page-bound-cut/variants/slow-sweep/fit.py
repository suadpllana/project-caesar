HEAD = 8
ENT = 2
KID = 2


def share(a, b):
    n = len(a)
    if len(b) < n:
        n = len(b)
    i = 0
    while i < n and a[i] == b[i]:
        i += 1
    return i


def span(first, last, count, total, kids):
    n = HEAD + kids * KID
    if count:
        pre = share(first, last)
        n += pre + count * ENT + total - count * pre
    return n


def hold(page):
    return page.keys if page.leaf else page.seps


def scan(ents):
    total = 0
    for e in ents:
        total += len(e)
    return len(ents), total


def bulk(tr, pid):
    page = tr.at(pid)
    ents = hold(page)
    count, total = scan(ents)
    kids = 0 if page.leaf else len(page.kids)
    if not count:
        return span("", "", 0, 0, kids)
    return span(ents[0], ents[-1], count, total, kids)


def over(tr, pid):
    return bulk(tr, pid) > tr.cap


def under(tr, pid):
    return bulk(tr, pid) < tr.floor
