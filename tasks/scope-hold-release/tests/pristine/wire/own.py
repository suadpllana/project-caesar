from wire.reg import SING
from wire.scope import ROOT
from wire import pin


def homes(tbl, st, batch, at):
    out = {}
    for i, nm, up in batch:
        r = tbl[nm]
        if r.life == SING:
            out[i] = ROOT
        elif r.tag:
            out[i] = pin.where(st, at, r.tag)
        else:
            out[i] = at
    return out
