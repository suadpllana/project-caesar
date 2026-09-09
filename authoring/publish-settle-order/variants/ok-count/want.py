from reg import hold


def _keepers(h):
    d = getattr(h, "keepers", None)
    if d is None:
        d = h.keepers = {}
    return d


def joined(h, r):
    keepers = _keepers(h)
    for other, kind in r.needs:
        if kind:
            keepers.setdefault(other, set()).add(r.name)


def tied(h, r, t):
    r.ties.append(t.name)
    _keepers(h).setdefault(t.name, set()).add(r.name)


def parted(h, r):
    keepers = _keepers(h)
    freed = []
    for other in [o for o, kind in r.needs if kind] + r.ties:
        who = keepers.get(other)
        if who is not None:
            who.discard(r.name)
            if not who:
                freed.append(other)
    r.ties = []
    return list(dict.fromkeys(freed))


def wanted(h, r):
    return hold.held(h, r.name) > 0 or bool(_keepers(h).get(r.name))
