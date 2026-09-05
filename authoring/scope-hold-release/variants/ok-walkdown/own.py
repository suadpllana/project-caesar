from wire.reg import SING
from wire.scope import ROOT


def homes(tbl, batch, at):
    kind = dict((i, tbl[nm].life) for i, nm, up in batch)
    kids = {}
    for i, nm, up in batch:
        kids.setdefault(up, []).append(i)
    out = {}
    stack = [(i, False) for i in sorted(kids.get(0, []))]
    while stack:
        i, deep = stack.pop()
        deep = deep or kind.get(i) == SING
        out[i] = ROOT if deep else at
        for c in sorted(kids.get(i, [])):
            stack.append((c, deep))
    for i in kind:
        out.setdefault(i, at)
    return out
