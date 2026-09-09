"""Which publications a caller is allowed to reach.

Two attributes per unit, and the whole of the scope model is that they are two and not one. A
publication is either public or private to the scope that brought it up; that is what `den`
answers, and it is what the buckets in `pick.py` are keyed by. A unit *reads* the public
publications plus the ones in the scope it was brought up into; that is what `home` answers, and
it is what `keys` is built from. They start equal and `act` on a private unit splits them: the
publication becomes public where it stands, and the unit goes on reading its scope. A unit brought
up by a call is published into the caller's `home`, not into whatever its publication has become.

Nothing else about a scope matters: it holds nothing up, it is not a unit, and it never appears
in the trace.
"""


def _tab(h, key):
    d = getattr(h, key, None)
    if d is None:
        d = {}
        setattr(h, key, d)
    return d


def fresh(h):
    h.scopes = getattr(h, "scopes", 0) + 1
    return h.scopes


def seal(h, r, den):
    _tab(h, "dens")[r.name] = den
    _tab(h, "homes")[r.name] = den


def open_up(h, r):
    _tab(h, "dens")[r.name] = None
    _tab(h, "homes")[r.name] = None


def den(h, r):
    return _tab(h, "dens").get(r.name)


def home(h, r):
    return _tab(h, "homes").get(r.name)


def keys(h, caller):
    mine = home(h, caller)
    return (None,) if mine is None else (None, mine)
