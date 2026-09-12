from hold import book, name, say


def rankof(h, req):
    return (0 if req[4] else 1, req[0])


def grantable(h, req):
    return not book.anyclash(h, req[1], req[2], req[3])


def file_(h, req):
    req[4] = 1 if book.holds_over(h, req[1], req[2]) else 0
    h.line.append(req)
    h.ask[req[1]] = req
    say.wait(h, req[1], req[2], req[3])


def give(h, req):
    fid, job, scope, mode = req[0], req[1], req[2], req[3]
    for one in list(h.held.get(job) or ()):
        if one != scope and book.covers(scope, one):
            book.lose(h, job, one)
    book.put(h, job, scope, mode)
    book.unfile(h, req)
    say.grant(h, job, scope, mode)


def settle(h, units):
    while True:
        moved = False
        for req in sorted(h.line, key=lambda r: rankof(h, r)):
            if req in h.line and grantable(h, req):
                give(h, req)
                moved = True
                break
        if not moved:
            return
