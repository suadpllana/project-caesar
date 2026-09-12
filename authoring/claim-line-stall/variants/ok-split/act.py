from hold import book, lift, line, name, say, turn


def take(h, job, scope, mode):
    if job in h.ask:
        return
    if book.covered(h, job, scope, mode):
        say.grant(h, job, scope, mode)
        return
    scope, mode = lift.raised(h, job, scope, mode)
    h.nfile += 1
    req = [h.nfile, job, scope, mode]
    book.wake(h, job)
    if line.grantable(h, req):
        line.give(h, req)
    else:
        line.file_(h, req)
    turn.after(h, ())


def drop(h, job, scope):
    gone = book.lose(h, job, scope)
    say.free(h, job, scope, book.owns(h, job))
    if not gone:
        return
    book.rest(h, job)
    turn.after(h, (name.cut(scope)[0],))


def over(h, job):
    n, where, had = book.clear(h, job)
    say.over(h, job, n)
    if n or had:
        turn.after(h, where)


def show(h, unit):
    say.show(h, unit, book.listing(h, unit), book.onunit(h, unit))
