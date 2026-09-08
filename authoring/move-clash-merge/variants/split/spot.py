"""A correct variant: survival settled where placement is, and no live.py at all."""
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




def alive(ag, lo, ro, raw):
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
        if mk(ag, side, nd.p) != a.p or nd.nm != a.nm or nd.c != a.c:
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
