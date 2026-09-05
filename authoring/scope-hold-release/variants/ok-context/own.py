from wire.reg import SING
from wire.scope import ROOT


def homes(tbl, batch, at):
    kind = {}
    par = {}
    for i, nm, up in batch:
        kind[i] = tbl[nm].life
        par[i] = up
    out = {}
    for i in sorted(par):
        j = i
        deep = False
        while j:
            if kind.get(j) == SING:
                deep = True
                break
            j = par.get(j, 0)
        out[i] = ROOT if deep else at
    return out
