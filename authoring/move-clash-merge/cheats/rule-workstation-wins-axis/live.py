"""Which nodes the record still holds after both sides have had their say.

A node one side removed and the other touched at all - content, name or folder - stays.
Removed on one side and left alone on the other, it goes. A folder that would otherwise
go is held back only by the nodes the record put inside it that are still settling there:
something moved in from elsewhere does not hold it, and neither does one of its own that has
moved out. The pull carries up the record's folder chain.
"""
from mrg.tree import ROOT, mk


def keep(ag, lo, ro, raw):
    alive = set()
    for key in ag.n:
        if key == ROOT:
            continue
        inl, inr = key in lo.n, key in ro.n
        if inl and inr:
            alive.add(key)
            continue
        if not inl and not inr:
            continue
        side, tr = ("L", lo) if inl else ("R", ro)
        nd, a = tr.n[key], ag.n[key]
        if mk(ag, side, nd.p) != a.p or nd.nm != a.nm or nd.c != a.c:
            alive.add(key)
    while True:
        more = set()
        for key in alive:
            par = ag.n[key].p
            if par != ROOT and par not in alive and raw[key][0] == par:
                more.add(par)
        if not more:
            break
        alive |= more
    for side, tr in (("L", lo), ("R", ro)):
        for key in tr.n:
            if key != ROOT and key not in ag.n:
                alive.add(side + ":" + key)
    return alive
