from mrg.tree import ROOT, mk


def pick(ag, lo, ro):
    out = {}
    for key in ag.n:
        if key == ROOT:
            continue
        inl, inr = key in lo.n, key in ro.n
        if not inl and not inr:
            continue
        a = ag.n[key]
        if inl and inr:
            lp, ln = mk(ag, "L", lo.n[key].p), lo.n[key].nm
            rp, rn = mk(ag, "R", ro.n[key].p), ro.n[key].nm
            if lp != a.p or ln != a.nm:
                out[key] = (lp, ln, "a" if lp == a.p else "L", "a" if ln == a.nm else "L")
            elif rp != a.p or rn != a.nm:
                out[key] = (rp, rn, "a" if rp == a.p else "R", "a" if rn == a.nm else "R")
            else:
                out[key] = (a.p, a.nm, "a", "a")
        elif inl:
            lp, ln = mk(ag, "L", lo.n[key].p), lo.n[key].nm
            out[key] = (lp, ln, "a" if lp == a.p else "L", "a" if ln == a.nm else "L")
        else:
            rp, rn = mk(ag, "R", ro.n[key].p), ro.n[key].nm
            out[key] = (rp, rn, "a" if rp == a.p else "R", "a" if rn == a.nm else "R")
    for side, tr in (("L", lo), ("R", ro)):
        for key in tr.n:
            if key == ROOT or key in ag.n:
                continue
            out[side + ":" + key] = (mk(ag, side, tr.n[key].p), tr.n[key].nm, side, side)
    return out


def loop(pl):
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
        back = ag.n[who].p if who in ag.n else ROOT
        pl[who] = (up(ag, alive, back), nm, "a", ns)
        pinned.add(who)
