"""Correct variant: the earliest grantable ask anywhere goes first, and then start again."""
from hold import book, name, say


def rankof(h, req):
    return (0 if book.holds_over(h, req[1], req[2]) else 1, req[0])


def earlier(h, req):
    out = set()
    mine = rankof(h, req)
    for fid, other in h.queue.get(name.cut(req[2])[0], {}).items():
        if fid == req[0] or other[1] == req[1]:
            continue
        if not book.overlap(req[2], other[2]) or not book.clash(req[3], other[3]):
            continue
        if rankof(h, other) < mine:
            out.add(other[1])
    return out


def ahead(h, req):
    return bool(earlier(h, req))


def grantable(h, req):
    if book.anyclash(h, req[1], req[2], req[3]):
        return False
    return not ahead(h, req)


def file_(h, req):
    h.ask[req[1]] = req
    book.recheck(h, req[1])
    h.queue.setdefault(name.cut(req[2])[0], {})[req[0]] = req
    say.wait(h, req[1], req[2], req[3])


def give(h, req):
    job, scope, mode = req[1], req[2], req[3]
    for one in list(book.mine_here(h, job, name.cut(scope)[0])):
        if one != scope and book.covers(scope, one):
            book.lose(h, job, one)
    book.put(h, job, scope, mode)
    book.unfile(h, req)
    say.grant(h, job, scope, mode)


def settle(h, units):
    while True:
        best = None
        for unit in units:
            for req in h.queue.get(unit, {}).values():
                if grantable(h, req):
                    got = rankof(h, req)
                    if best is None or got < best[0]:
                        best = (got, req)
        if best is None:
            return
        give(h, best[1])
