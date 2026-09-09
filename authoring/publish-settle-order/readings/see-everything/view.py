def _dens(h):
    d = getattr(h, "dens", None)
    if d is None:
        d = h.dens = {}
    return d


def fresh(h):
    h.scopes = getattr(h, "scopes", 0) + 1
    return h.scopes


def seal(h, r, den):
    _dens(h)[r.name] = den


def open_up(h, r):
    _dens(h)[r.name] = None


def den(h, r):
    return _dens(h).get(r.name)


def keys(h, caller):
    return tuple(dict.fromkeys([None] + list(_dens(h).values())))
