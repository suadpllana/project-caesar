from wire.reg import SING
from wire.scope import ROOT
from wire import pin


def homes(tbl, st, batch, at):
    kind = {}
    par = {}
    for i, nm, up in batch:
        kind[i] = tbl[nm].life
        par[i] = up
    name = dict((i, nm) for i, nm, _u in batch)
    out = {}
    for i in sorted(par):
        j = i
        deep = False
        while j:
            if kind.get(j) == SING:
                deep = True
                break
            j = par.get(j, 0)
        if deep:
            out[i] = ROOT
            continue
        tag = tbl[name[i]].tag
        out[i] = pin.where(st, at, tag) if tag else at
    return out
