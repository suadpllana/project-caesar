from wire.reg import SING
from wire.scope import ROOT


def homes(tbl, batch, at):
    out = {}
    for i, nm, up in batch:
        out[i] = ROOT if tbl[nm].life == SING else at
    return out
