"""Turning a settled record into operations a side can actually carry out.

Nothing is emitted before it can be done. A destination folder counts only when the
path names the node the record puts the child under, not merely something with the
right name, and the destination name has to be unused - case-blind on the server side.
When nothing can be done and the side is still not the record, whatever is sitting on
the wanted name is pushed aside under a mark, and the round carries on - including the
node itself, which is how a name changes case on a side that compares names case-blind.
"""
from mrg import lay
from mrg.tree import ROOT

RANK = {"rm": 0, "mv": 1, "mkd": 2, "mkf": 2, "ed": 3}
LIMIT = 4000


def num(key):
    try:
        return (0, int(key))
    except ValueError:
        return (1, key)


def spot(work, tgt, inv, tk):
    par = tgt.n[tk].p
    if par == ROOT:
        return ROOT
    return inv.get(par)


def ready(work, tgt, m, inv, fold):
    out = []
    for ck in work.n:
        if ck == ROOT or ck in m or work.kids(ck):
            continue
        out.append((("rm", work.path(ck)), None))
    for ck, tk in m.items():
        if ck == ROOT:
            continue
        nd, td = work.n[ck], tgt.n[tk]
        want = spot(work, tgt, inv, tk)
        if td.k == "f" and nd.c != td.c:
            out.append((("ed", work.path(ck), td.c), None))
        if nd.p == want and nd.nm == td.nm:
            continue
        if want is None or want not in work.n:
            continue
        if work.under(want, ck) or not work.free(want, td.nm, fold):
            continue
        out.append((("mv", work.path(ck), lay.join(work.path(want), td.nm)), None))
    for tk in tgt.n:
        if tk == ROOT or tk in inv:
            continue
        td = tgt.n[tk]
        want = spot(work, tgt, inv, tk)
        if want is None or want not in work.n:
            continue
        if not work.free(want, td.nm, fold):
            continue
        dst = lay.join(work.path(want), td.nm)
        op = ("mkd", dst) if td.k == "d" else ("mkf", dst, td.c)
        out.append((op, tk))
    return out


def aside(work, tgt, m, inv, fold):
    best = None
    for tk in tgt.n:
        if tk == ROOT:
            continue
        want = spot(work, tgt, inv, tk)
        if want is None or want not in work.n:
            continue
        ck = inv.get(tk)
        if ck is not None and work.n[ck].p == want and work.n[ck].nm == tgt.n[tk].nm:
            continue
        for other in work.kids(want):
            got = work.n[other].nm
            if got == tgt.n[tk].nm or (fold and got.lower() == tgt.n[tk].nm.lower()):
                cand = (num(tk), work.path(other))
                if best is None or cand < best:
                    best = cand
    if best is None:
        return None
    where = best[1]
    ck = work.at(where)
    par = work.n[ck].p
    k = 1
    while not work.free(par, "~t%d" % k, fold):
        k += 1
    return ("mv", where, lay.join(work.path(par), "~t%d" % k))


def take(work, tgt, m, inv, op, tk, fold):
    if tk is None:
        lay.do(work, op, fold, lambda: "z")
        return
    par, nm = lay.split(op[1])
    pk = work.at(par)
    work.put("t:" + tk, tgt.n[tk].k, pk, nm, tgt.n[tk].c)
    m["t:" + tk] = tk
    inv[tk] = "t:" + tk


def plan(cur, tgt, m, fold):
    work = cur.copy()
    m = dict((k, v) for k, v in m.items() if k in work.n)
    inv = dict((v, k) for k, v in m.items())
    ops = []
    for _ in range(LIMIT):
        pick = None
        for op, tk in ready(work, tgt, m, inv, fold):
            key = (RANK[op[0]], op[1])
            if pick is None or key < pick[0]:
                pick = (key, op, tk)
        if pick is None:
            op = aside(work, tgt, m, inv, fold)
            if op is None:
                return ops
            ops.append(op)
            take(work, tgt, m, inv, op, None, fold)
            continue
        ops.append(pick[1])
        take(work, tgt, m, inv, pick[1], pick[2], fold)
    return ops
