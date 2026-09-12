"""The waiting line: its order, the refusal test, and the settling pass.

The order is not stored. An ask stands ahead of the line exactly while its job holds a claim
overlapping what the ask asked for, which is read off the book at the moment the order is
needed rather than recorded on the ask: an ordinary drop, a whole-unit claim swallowing the
job's cell claims, and a cancellation all change it under an ask that is already waiting.
Filing order breaks ties inside each group.

Settling walks the asks on the units something was just released from, in that order, and
grants each one that is grantable when it is reached. Restarting from the top of the whole
line after every grant is also correct and is the family the execution limit rules out: a
grant only ever adds or strengthens a claim, and a claim a job gives up when a whole-unit
claim swallows it is covered by that claim, so no grant can make an ask earlier in the order
grantable. One pass is therefore complete.
"""
from hold import book, name, say


def rankof(h, req):
    return (0 if book.holds_over(h, req[1], req[2]) else 1, req[0])


def ahead(h, req):
    """Does an ask of another job standing ahead of this one conflict with it?"""
    mine = rankof(h, req)
    box = h.byunit.get(name.cut(req[2])[0])
    if not box:
        return False
    for fid, other in box.items():
        if fid == req[0] or other[1] == req[1]:
            continue
        if not book.overlap(req[2], other[2]) or not book.clash(req[3], other[3]):
            continue
        if rankof(h, other) < mine:
            return True
    return False


def grantable(h, req):
    if book.anyclash(h, req[1], req[2], req[3]):
        return False
    return not ahead(h, req)


def file_(h, req):
    h.line[req[0]] = req
    h.ask[req[1]] = req
    h.byunit.setdefault(name.cut(req[2])[0], {})[req[0]] = req
    book.recheck(h, req[1])
    say.wait(h, req[1], req[2], req[3])


def give(h, req):
    fid, job, scope, mode = req
    for s in list(h.held.get(job) or ()):
        if s != scope and book.covers(scope, s):
            book.lose(h, job, s)
    book.put(h, job, scope, mode)
    book.unfile(h, req)
    book.recheck(h, job)
    say.grant(h, job, scope, mode)


def settle(h, units):
    while True:
        order = sorted(h.line.values(), key=lambda r: rankof(h, r))
        moved = False
        for req in order:
            if req[0] in h.line and grantable(h, req):
                give(h, req)
                moved = True
                break
        if not moved:
            return
