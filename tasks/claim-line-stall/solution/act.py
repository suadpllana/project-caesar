"""The four ops.

Order matters here. An ask that is already covered changes nothing and is never filed, so it
cannot be raised either. Raising happens before the refusal test, so what is tested and what
is printed is the whole-unit ask. Settling runs only after something was released, because a
grant cannot make an earlier ask grantable. The stall search runs after every op that filed
an ask or moved a claim, and each cancellation releases claims, which is why it settles and
looks again.
"""
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
    say.free(h, job, scope, len(h.held.get(job) or ()))
    if not gone:
        return
    book.recheck(h, job)
    book.rest(h, job)
    turn.after(h, (name.cut(scope)[0],))


def over(h, job):
    n, where, had = book.clear(h, job)
    say.over(h, job, n)
    if n or had:
        turn.after(h, where)


def show(h, unit):
    say.show(h, unit, book.listing(h, unit), book.onunit(h, unit))
