from mrg import book, lay, read, step
from mrg.tree import ROOT, Tr


class Mint:
    __slots__ = ("seq",)

    def __init__(self):
        self.seq = 0

    def __call__(self):
        self.seq += 1
        return "u%d" % self.seq


def rekey(cur, tgt, mint):
    out = Tr()
    seen = {}
    for p, k in cur.paths():
        par, nm = lay.split(p)
        pk = seen[par] if par != "/" else ROOT
        nd = cur.n[k]
        tk = tgt.at(p)
        if tk is None or tgt.n[tk].k != nd.k:
            tk = mint()
        out.put(tk, nd.k, pk, nm, nd.c)
        seen[p] = tk
    return out


def go(lines, put):
    base, nxt, rounds = read.parse(lines)
    ag = base
    lo, ro = base.copy(), base.copy()
    mint = Mint()
    for i, (lops, rops) in enumerate(rounds, 1):
        for op in lops:
            lay.do(lo, op, False, mint)
        for op in rops:
            lay.do(ro, op, True, mint)
        tgt, nxt, ml, mr = book.round(ag, nxt, lo, ro)
        for tag, cur, m, fold in (("L", lo, ml, False), ("R", ro, mr, True)):
            for op in step.plan(cur, tgt, m, fold):
                put("%d %s %s" % (i, tag, lay.fmt(op)))
                lay.do(cur, op, fold, mint)
        lo = rekey(lo, tgt, mint)
        ro = rekey(ro, tgt, mint)
        for tag, cur in (("l", lo), ("r", ro)):
            for p, k in cur.paths():
                nd = cur.n[k]
                put("%d %s %s %s" % (i, tag, p, nd.c if nd.k == "f" else "-"))
        ag = tgt
