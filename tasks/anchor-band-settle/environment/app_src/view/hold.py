from view import lay, pick


def start(v):
    v.keep = None


def before(v):
    fl = lay.flow(v)
    b = pick.first(v, fl, v.s)
    v.keep = None if b is None else (b, fl.top[b] - v.s)


def after(v):
    fl = lay.flow(v)
    top = lay.span(v, fl)
    ask = None
    for kind, _b, arg in v.log:
        if kind == "to":
            ask = arg
    if ask is not None:
        return min(max(ask, 0), top), "off scroll"
    s = min(max(v.s, 0), top)
    if v.keep is None:
        return s, "none"
    b, d = v.keep
    if b.gone or b not in fl.top:
        b = pick.first(v, fl, s)
        return s, "none" if b is None else b.id
    return min(max(fl.top[b] - d, 0), top), b.id
