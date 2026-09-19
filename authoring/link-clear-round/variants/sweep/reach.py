"""Variant: full sweeps over the links until nothing moves.

No worklist and no table order: every link is tried against every row the change carries, and
the sweep runs again whenever a group or a new key changed, which is what settles a row that a
longer chain reaches later.
"""
from keep import meld


def walk(work, kind, tab, key, new):
    grp = {(tab, key): 0}
    carry = {(tab, key): new}
    hits = {}
    bars = {}
    moving = True
    while moving:
        moving = False
        for li, ln in enumerate(work.links):
            act = ln.goes if kind == "out" else ln.moves
            if act == "wait":
                continue
            ups = [k for (t, k) in carry if t == ln.par]
            if not ups:
                continue
            for ck in work.find.kids(li, ups):
                up = work.st.get(ln.kid, ck)[ln.ci]
                if act == "bar":
                    bars[(li, ck)] = ln.kid
                    continue
                seat = (ln.kid, ck)
                deep = grp[(ln.par, up)] + 1
                if grp.get(seat, -1) < deep:
                    grp[seat] = deep
                    moving = True
                hits[(seat, li)] = (ln.ci, act, carry[(ln.par, up)])
                if act == "drop":
                    if seat not in carry:
                        carry[seat] = None
                        moving = True
                elif act == "follow" and ln.ci == 0:
                    best = min(i for (s, i) in hits
                               if s == seat and hits[(s, i)][0] == 0
                               and hits[(s, i)][1] == "follow")
                    val = hits[(seat, best)][2]
                    if seat not in carry or carry[seat] != val:
                        carry[seat] = val
                        moving = True
    return meld.melt(hits, kind, tab, key, new), grp, sorted(bars), bars
