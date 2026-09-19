"""Variant: a worklist relaxed until neither a group nor a new key moves again.

It knows nothing about the order the tables sit in. A row re-reached by a longer chain goes
back on the list, and so does every row reached from it, until the marks stop changing.
"""
from keep import meld


def walk(work, kind, tab, key, new):
    grp = {(tab, key): 0}
    carry = {(tab, key): new}
    stamp = {}
    edge = {}
    bars = []
    todo = [(tab, key)]
    while todo:
        seat = todo.pop()
        mark = (grp[seat], carry.get(seat))
        if stamp.get(seat) == mark:
            continue
        stamp[seat] = mark
        ptab, pkey = seat
        for li, ln in work.fan.get(ptab, ()):
            act = ln.goes if kind == "out" else ln.moves
            if act == "wait":
                continue
            for ck in work.find.kids(ln, (pkey,)):
                if act == "bar":
                    bars.append((li, ln.kid, ck))
                    continue
                under = (ln.kid, ck)
                edge[(ln.kid, ck, li)] = (ln.ci, act, mark[1])
                if grp.get(under, -1) < mark[0] + 1:
                    grp[under] = mark[0] + 1
                if act == "drop":
                    carry.setdefault(under, None)
                    todo.append(under)
                elif act == "follow" and ln.ci == 0:
                    best = min((i, v) for (t, k, i), (c, a, v) in edge.items()
                               if (t, k) == under and c == 0 and a == "follow")
                    carry[under] = best[1]
                    todo.append(under)
                elif under in carry:
                    todo.append(under)
    return meld.melt(edge, kind, tab, key, new), grp, bars
