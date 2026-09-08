"""The record: what each node holds, which numbers the new ones get, and the maps back.

The order here is the part the shipped engine has wrong. A file both sides wrote leaves
a second node behind carrying the other side's bytes, and that node has to exist, and
have a number, before the folder's names are settled - otherwise it cannot take part in
the contest it caused. Numbers go out in one pass: the server's new nodes in path order,
then the workstation's, then the leftover copies, and the counter never goes back.
"""
from mrg import live, name, spot
from mrg.tree import ROOT, Tr, mk


def hold(ag, lo, ro, pl):
    con = {}
    copies = []
    for key in pl:
        if key in ag.n:
            a = ag.n[key]
            if a.k == "d":
                con[key] = None
                continue
            inl, inr = key in lo.n, key in ro.n
            lc = lo.n[key].c if inl else None
            rc = ro.n[key].c if inr else None
            if inl and inr:
                if lc == rc or rc == a.c:
                    con[key] = lc
                elif lc == a.c:
                    con[key] = rc
                else:
                    con[key] = lc
                    copies.append(key)
            else:
                con[key] = lc if inl else rc
        else:
            side, k = key.split(":", 1)
            tr = lo if side == "L" else ro
            con[key] = tr.n[k].c
    return con, sorted(copies, key=spot.rank)


def number(ag, lo, ro, pl, copies, nxt):
    ids = dict((k, k) for k in pl if k in ag.n)
    fresh = []
    for side, tr in (("L", lo), ("R", ro)):
        news = sorted((tr.path(k), side + ":" + k)
                      for k in tr.n if k != ROOT and k not in ag.n)
        fresh += [key for _, key in news]
    fresh += ["C:" + k for k in copies]
    for key in fresh:
        if key in pl:
            ids[key] = str(nxt)
            nxt += 1
    return ids, nxt


def kind(ag, lo, ro, key):
    if key.startswith("C:"):
        return "f"
    if key in ag.n:
        return ag.n[key].k
    side, k = key.split(":", 1)
    return (lo if side == "L" else ro).n[k].k


def build(ag, lo, ro, pl, nms, con, ids):
    tgt = Tr()
    left = list(pl)
    while left:
        again = []
        for key in left:
            par = pl[key][0]
            pk = ROOT if par == ROOT else ids.get(par)
            if pk is None or pk not in tgt.n:
                again.append(key)
                continue
            tgt.put(ids[key], kind(ag, lo, ro, key), pk, nms[key], con[key])
        if len(again) == len(left):
            break
        left = again
    return tgt


def round(ag, nxt, lo, ro):
    raw = spot.pick(ag, lo, ro)
    alive = live.keep(ag, lo, ro, raw)
    pl = spot.fix(ag, alive, raw)
    con, copies = hold(ag, lo, ro, pl)
    for key in copies:
        c = "C:" + key
        pl[c] = (pl[key][0], pl[key][1], "c", "c")
        con[c] = ro.n[key].c
    ids, nxt2 = number(ag, lo, ro, pl, copies, nxt)
    nms = name.settle(ag, lo, ro, pl, ids)
    tgt = build(ag, lo, ro, pl, nms, con, ids)
    maps = []
    for side, tr in (("L", lo), ("R", ro)):
        m = {ROOT: ROOT}
        for key in tr.n:
            if key == ROOT:
                continue
            got = ids.get(mk(ag, side, key))
            if got is not None and got in tgt.n:
                m[key] = got
        maps.append(m)
    return tgt, nxt2, maps[0], maps[1]
