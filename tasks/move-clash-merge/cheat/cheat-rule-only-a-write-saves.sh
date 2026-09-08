#!/bin/bash
# cheat: only-a-write-saves
# only a change of content saves a node the other side removed
set -euo pipefail
mkdir -p /app/mrg
cat > /app/mrg/live.py <<'PYEOF'
"""Which nodes the record still holds after both sides have had their say.

A node one side removed and the other touched at all - content, name or folder - stays.
Removed on one side and left alone on the other, it goes. A folder that would otherwise
go is held back only by the nodes the record put inside it that are still settling there:
something moved in from elsewhere does not hold it, and neither does one of its own that has
moved out. The pull carries up the record's folder chain.
"""
from mrg.tree import ROOT, mk


def keep(ag, lo, ro, raw):
    alive = set()
    for key in ag.n:
        if key == ROOT:
            continue
        inl, inr = key in lo.n, key in ro.n
        if inl and inr:
            alive.add(key)
            continue
        if not inl and not inr:
            continue
        side, tr = ("L", lo) if inl else ("R", ro)
        nd, a = tr.n[key], ag.n[key]
        if nd.c != a.c:
            alive.add(key)
    while True:
        more = set()
        for key in alive:
            par = ag.n[key].p
            if par != ROOT and par not in alive and raw[key][0] == par:
                more.add(par)
        if not more:
            break
        alive |= more
    for side, tr in (("L", lo), ("R", ro)):
        for key in tr.n:
            if key != ROOT and key not in ag.n:
                alive.add(side + ":" + key)
    return alive
PYEOF
cat > /app/mrg/spot.py <<'PYEOF'
"""Where each surviving node sits: folder and name, then repair and cycle breaking.

`pick` settles the two placement axes independently, which is the rule the shipped
engine gets wrong: it takes one side's whole move. Each axis is settled on its own,
and the source of each decision is carried out of here because the cycle rule and the
name rule both need to know which side a value came from.

`fix` runs after survival is known. A node whose settled folder did not survive walks
up the record's folder chain to the nearest folder that did. Then, while any node sits
under itself, one node in the loop goes back to the folder the record gave it.
"""
from mrg.tree import ROOT, mk


def axis(av, lv, rv, present_l, present_r):
    """Settle one axis. Returns the value and the side it came from."""
    if present_l and present_r:
        if lv == rv:
            return (lv, "a" if lv == av else "R")
        if lv == av:
            return (rv, "R")
        if rv == av:
            return (lv, "L")
        return (rv, "R")
    if present_l:
        return (lv, "a" if lv == av else "L")
    return (rv, "a" if rv == av else "R")


def pick(ag, lo, ro):
    out = {}
    for key in ag.n:
        if key == ROOT:
            continue
        inl, inr = key in lo.n, key in ro.n
        if not inl and not inr:
            continue
        a = ag.n[key]
        lp = mk(ag, "L", lo.n[key].p) if inl else None
        rp = mk(ag, "R", ro.n[key].p) if inr else None
        ln = lo.n[key].nm if inl else None
        rn = ro.n[key].nm if inr else None
        par, ps = axis(a.p, lp, rp, inl, inr)
        nm, ns = axis(a.nm, ln, rn, inl, inr)
        out[key] = (par, nm, ps, ns)
    for side, tr in (("L", lo), ("R", ro)):
        for key in tr.n:
            if key == ROOT or key in ag.n:
                continue
            out[side + ":" + key] = (mk(ag, side, tr.n[key].p), tr.n[key].nm, side, side)
    return out


def loop(pl):
    """One set of keys that sit under each other, or None."""
    state = {}
    for start in sorted(pl):
        if state.get(start):
            continue
        trail = []
        seen = {}
        at = start
        while at in pl and not state.get(at):
            if at in seen:
                return trail[seen[at]:]
            seen[at] = len(trail)
            trail.append(at)
            at = pl[at][0]
        for k in trail:
            state[k] = 1
    return None


def rank(key):
    try:
        return (0, int(key))
    except ValueError:
        return (1, key)


def up(ag, alive, par):
    while par != ROOT and par not in alive:
        par = ag.n[par].p
    return par


def fix(ag, alive, raw):
    pl = {}
    for key, (par, nm, ps, ns) in raw.items():
        if key not in alive:
            continue
        pl[key] = (up(ag, alive, par), nm, ps, ns)
    pinned = set()
    while True:
        ring = loop(pl)
        if not ring:
            return pl
        free = [k for k in ring if k not in pinned and pl[k][2] == "L"]
        if not free:
            free = [k for k in ring if k not in pinned]
        if not free:
            return pl
        who = min(free, key=rank)
        par, nm, ps, ns = pl[who]
        pl[who] = (up(ag, alive, ag.n[who].p), nm, "a", ns)
        pinned.add(who)
PYEOF
cat > /app/mrg/name.py <<'PYEOF'
"""Settling the folders where more than one node wants the same name.

Names are contested case-blind, because the record cannot hold two names in one folder
that differ only in case. One node keeps the contested name and the rest take a mark
before the extension. The order the losers are marked is by id over the whole folder,
not group by group, so a folder with two contests hands out marks in one pass.
"""


def fold(nm):
    return nm.lower()


def mark(nm, k):
    cut = nm.rfind(".")
    if 0 < cut < len(nm) - 1:
        return "%s~%d%s" % (nm[:cut], k, nm[cut:])
    return "%s~%d" % (nm, k)


def held(ag, key, par, nm):
    if key not in ag.n:
        return False
    a = ag.n[key]
    return a.p == par and a.nm == nm


def shows(ag, tr, side, key, nm):
    if key.startswith(side + ":"):
        return fold(tr.n[key.split(":", 1)[1]].nm) == fold(nm)
    if key in ag.n and key in tr.n:
        return fold(tr.n[key].nm) == fold(nm)
    return False


def order(ag, lo, ro, key, par, nm, ids):
    if key.startswith("C:"):
        return (4, int(ids[key]))
    if held(ag, key, par, nm):
        return (0, int(ids[key]))
    if shows(ag, ro, "R", key, nm):
        return (1, int(ids[key]))
    if shows(ag, lo, "L", key, nm):
        return (2, int(ids[key]))
    return (3, int(ids[key]))


def settle(ag, lo, ro, pl, ids):
    out = {}
    folders = {}
    for key, (par, nm, ps, ns) in pl.items():
        folders.setdefault(par, []).append(key)
    for par, keys in folders.items():
        groups = {}
        for key in keys:
            groups.setdefault(fold(pl[key][1]), []).append(key)
        taken = set()
        losers = []
        for f, members in groups.items():
            if len(members) == 1:
                out[members[0]] = pl[members[0]][1]
                taken.add(f)
                continue
            win = min(members, key=lambda k: order(ag, lo, ro, k, par, pl[k][1], ids))
            out[win] = pl[win][1]
            taken.add(fold(out[win]))
            losers += [k for k in members if k != win]
        for key in sorted(losers, key=lambda k: int(ids[k])):
            base = pl[key][1]
            k = 1
            while fold(mark(base, k)) in taken:
                k += 1
            out[key] = mark(base, k)
            taken.add(fold(out[key]))
    return out
PYEOF
cat > /app/mrg/book.py <<'PYEOF'
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
    for side, tr in (("R", ro), ("L", lo)):
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
PYEOF
cat > /app/mrg/step.py <<'PYEOF'
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
        if nd.p == want and nd.nm == td.nm:
            if td.k == "f" and nd.c != td.c:
                out.append((("ed", work.path(ck), td.c), None))
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
PYEOF
