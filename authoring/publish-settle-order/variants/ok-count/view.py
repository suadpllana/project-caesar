class _Scope:
    __slots__ = ("den", "home")

    def __init__(self, den):
        self.den = den
        self.home = den


def _of(h):
    d = getattr(h, "scope_of", None)
    if d is None:
        d = h.scope_of = {}
    return d


def fresh(h):
    h.scopes = getattr(h, "scopes", 0) + 1
    return h.scopes


def seal(h, r, den):
    _of(h)[r.name] = _Scope(den)


def open_up(h, r):
    _of(h)[r.name].den = None


def den(h, r):
    s = _of(h).get(r.name)
    return None if s is None else s.den


def home(h, r):
    s = _of(h).get(r.name)
    return None if s is None else s.home


def keys(h, caller):
    mine = home(h, caller)
    return (None,) if mine is None else (None, mine)
