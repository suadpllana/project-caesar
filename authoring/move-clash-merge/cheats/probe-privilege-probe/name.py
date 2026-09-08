def mark(nm, k):
    return "%s~%d" % (nm, k)


def held(ag, key, par, nm):
    if key not in ag.n:
        return False
    a = ag.n[key]
    return a.p == par and a.nm == nm


def shows(ag, tr, side, key, nm):
    if key.startswith(side + ":"):
        return tr.n[key.split(":", 1)[1]].nm == nm
    if key in ag.n and key in tr.n:
        return tr.n[key].nm == nm
    return False


def order(ag, lo, ro, key, par, nm, ids):
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
            groups.setdefault(pl[key][1], []).append(key)
        taken = set()
        losers = []
        for f, members in groups.items():
            if len(members) == 1:
                out[members[0]] = pl[members[0]][1]
                taken.add(f)
                continue
            win = min(members, key=lambda k: order(ag, lo, ro, k, par, pl[k][1], ids))
            out[win] = pl[win][1]
            taken.add(out[win])
            losers += [k for k in members if k != win]
        for key in sorted(losers, key=lambda k: int(ids[k])):
            base = pl[key][1]
            k = 1
            while mark(base, k) in taken:
                k += 1
            out[key] = mark(base, k)
            taken.add(out[key])
    return out
