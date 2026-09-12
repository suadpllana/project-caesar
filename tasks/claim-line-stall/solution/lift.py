"""Raising a cell ask to the whole unit.

Four cell claims already held in one unit and the next ask in that unit stops being an ask
for a cell: it becomes an ask for the unit, in the strongest mode the job would then need.
The job keeps every one of those cell claims while the raised ask waits, which is the whole
of why a raised ask that is refused can be the thing that closes a loop - it is holding
exactly what the jobs it is waiting for are asking for.
"""
from hold import book, name


def raised(h, job, scope, mode):
    u, c = name.cut(scope)
    if c is None:
        return scope, mode
    pair = h.tally.get(u, {}).get(job)
    if not pair or pair[0] + pair[1] < 4:
        return scope, mode
    out = mode
    if pair[1]:
        out = "w"
    if h.own.get(u, {}).get(job) == "w":
        out = "w"
    return u, book.strongest(out)
