"""Which gauge settles next.

The requirement is that a gauge never runs on a value that moves again later in the
same round, and never runs twice in one round. That is a statement about ORDER: a gauge
may run only once everything it reads has already taken its final value for the round.

So the queue is not a queue. Entries come out in order of how far each one sits from
the feeds - a gauge one step from a feed before a gauge two steps from one - and among
gauges equally far, the earliest declared. `rk` is that distance, and it is maintained
by wire.tie rather than here, because only the moment a gauge has just been evaluated
tells you what it actually reads.

A feed is distance 0 by definition. A gauge whose distance has never been established
is provisionally 1, which is the smallest a gauge can be; wire.tie corrects it upward
the first time the gauge runs.
"""

import heapq


def start(net):
    return {"q": [], "in": set(), "tr": set(), "rk": {}}


def far(pl, net, n):
    if net.kind[n] == "f":
        return 0
    return pl["rk"].get(n, 1)


def wake(pl, net, g):
    if g in pl["in"]:
        return
    pl["in"].add(g)
    heapq.heappush(pl["q"], (far(pl, net, g), net.ix[g], g))


def take(pl, net):
    q = pl["q"]
    while q:
        r, i, g = heapq.heappop(q)
        if g not in pl["in"]:
            continue
        cur = far(pl, net, g)
        if r != cur:
            # The gauge was pushed at a distance that has since been corrected upward.
            # Re-file it under the distance it actually has now.
            heapq.heappush(q, (cur, net.ix[g], g))
            continue
        pl["in"].discard(g)
        return g
    return None
