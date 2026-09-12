"""Correct variant: the line as two sequences, re-derived whenever it is read."""
from hold import book, name, say


def rankof(h, req):
    return (0 if book.holds_over(h, req[1], req[2]) else 1, req[0])


def sort_unit(h, unit):
    box = h.byunit.get(unit)
    if not box:
        return []
    front, back = [], []
    for fid in sorted(box):
        (front if book.holds_over(h, box[fid][1], box[fid][2]) else back).append(box[fid])
    return front + back


def earlier(h, req):
    out = set()
    for other in sort_unit(h, name.cut(req[2])[0]):
        if other[0] == req[0]:
            break
        if other[1] == req[1]:
            continue
        if book.overlap(req[2], other[2]) and book.clash(req[3], other[3]) \
                and rankof(h, other) < rankof(h, req):
            out.add(other[1])
    return out


def ahead(h, req):
    mine = rankof(h, req)
    for other in sort_unit(h, name.cut(req[2])[0]):
        if rankof(h, other) >= mine:
            break
        if other[1] == req[1]:
            continue
        if book.overlap(req[2], other[2]) and book.clash(req[3], other[3]):
            return True
    return False


def grantable(h, req):
    if book.anyclash(h, req[1], req[2], req[3]):
        return False
    return not ahead(h, req)


def file_(h, req):
    h.ask[req[1]] = req
    book.recheck(h, req[1])
    h.byunit.setdefault(name.cut(req[2])[0], {})[req[0]] = req
    say.wait(h, req[1], req[2], req[3])


def give(h, req):
    job, scope, mode = req[1], req[2], req[3]
    for one in list((h.byjob.get(job) or {})):
        if one != scope and book.covers(scope, one):
            book.lose(h, job, one)
    book.put(h, job, scope, mode)
    book.unfile(h, req)
    say.grant(h, job, scope, mode)


def settle(h, units):
    rows = []
    for unit in units:
        rows.extend(h.byunit.get(unit, {}).values())
    rows.sort(key=lambda r: rankof(h, r))
    for req in rows:
        if req[1] in h.ask and h.ask[req[1]] is req and grantable(h, req):
            give(h, req)
