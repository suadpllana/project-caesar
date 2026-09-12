"""What the service does after an op.

Settling runs only when something was released, because a grant cannot make an ask standing
earlier in the order grantable: it only ever adds or strengthens a claim, and a claim a job
gives up when a whole-unit claim swallows it is covered by that claim. The stall search runs
after every op that could have changed what refuses what - every op that filed an ask, granted
one, or released a claim. An op that changes nothing can create no loop, so it is not asked.
Each cancellation releases claims, which is why it settles and looks again.
"""
from hold import book, knot, line, say


def after(h, units):
    if units:
        line.settle(h, units)
    while True:
        bad = knot.loops(h)
        if not bad:
            return
        gone = knot.pick(h, bad)
        n, where, _had = book.clear(h, gone)
        say.stop(h, gone, n)
        line.settle(h, where)
