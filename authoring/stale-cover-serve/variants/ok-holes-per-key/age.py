"""Retention.

A stretch whose validity ended is still worth keeping, because a read with an allowance is
answered from exactly those - but only back as far as the horizon, so once its last correct
version falls below the present version minus the horizon it can never be chosen again and
goes. A stretch that is still current has no end and is never discarded here.
"""


def sweep(tb, now, horizon):
    floor = now - horizon
    if floor <= 0:
        return
    tb.drop(floor)
