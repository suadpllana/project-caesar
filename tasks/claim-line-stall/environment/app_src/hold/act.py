from hold import book, lift, line, name, say, turn


def take(h, job, scope, mode):
    if job in h.ask:
        return
    if book.covered(h, job, scope, mode):
        say.grant(h, job, scope, mode)
        return
    scope, mode = lift.raised(h, job, scope, mode)
    h.nfile += 1
    req = [h.nfile, job, scope, mode, 0]
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
    turn.after(h, (name.cut(scope)[0],))


def over(h, job):
    units = set()
    mine = list((h.held.get(job) or {}).items())
    for one, _mode in mine:
        units.add(name.cut(one)[0])
        book.lose(h, job, one)
    say.over(h, job, len(mine))
    if mine:
        turn.after(h, units)


def show(h, unit):
    say.show(h, unit, book.listing(h, unit), book.onunit(h, unit))
