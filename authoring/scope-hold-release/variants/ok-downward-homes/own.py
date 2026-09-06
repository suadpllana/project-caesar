from wire.reg import SING
from wire.scope import ROOT
from wire import pin


def homes(tbl, st, batch, at):
    rows = {i: (nm, up) for i, nm, up in batch}
    kids = {i: [] for i in rows}
    roots = []
    for i, (_nm, up) in rows.items():
        if up in kids:
            kids[up].append(i)
        else:
            roots.append(i)

    out = {}

    def settle(i, rooted):
        nm, _up = rows[i]
        deep = rooted or tbl[nm].life == SING
        if deep:
            out[i] = ROOT
        elif tbl[nm].tag:
            out[i] = pin.where(st, at, tbl[nm].tag)
        else:
            out[i] = at
        for child in kids[i]:
            settle(child, deep)

    for root in roots:
        settle(root, False)
    return out
