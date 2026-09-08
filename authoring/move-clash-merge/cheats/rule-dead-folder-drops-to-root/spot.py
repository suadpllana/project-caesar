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
    return par if par == ROOT or par in alive else ROOT


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
