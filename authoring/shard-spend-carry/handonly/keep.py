"""Checkpoints: the value and moment of every slot of the map, in flat order.

Nothing in that sequence names a parameter, so it means what the map meant when it was
written. The map moves - a thaw sends a parameter to the end, a freeze takes one out - so
restoring against the map standing now puts other parameters' numbers into a parameter.
The layout is therefore recorded with the checkpoint and the saved runs are spliced back
across boundaries that no longer line up with anything live.
"""
from opt import cell


def init(r):
    r.ck = {}


def save(r, tag):
    cell._mark(r, "save %s" % tag)
    rows = []
    for name in r.map:
        rows.extend(r.par[name].keep())
    r.ck[tag] = ([(n, r.par[n].n) for n in r.map], rows)


def load(r, tag):
    cell._mark(r, "load %s" % tag)
    plan, rows = r.ck[tag]
    i = at = 0
    for name, n in plan:
        got = []
        left = n
        while left:
            cnt, v, m = rows[i]
            k = cnt - at
            if k > left:
                k = left
            got.append((k, v, m))
            at += k
            left -= k
            if at == cnt:
                i += 1
                at = 0
        r.par[name].put(got)
