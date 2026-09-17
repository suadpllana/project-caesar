from . import reach
from .store import Rec


def _mine(rec, name):
    touch = getattr(rec, "touch", None)
    return touch(name) if touch is not None else rec.get(name)


def one(rec, c):
    if c.kind == "new":
        if c.a in rec:
            return
        if c.b != "-" and c.b not in rec:
            return
        rec[c.a] = Rec(None if c.b == "-" else c.b)
        return
    if c.a not in rec:
        return
    if c.kind == "set":
        _mine(rec, c.a).fld[c.b] = c.c
    elif c.kind == "add":
        r = _mine(rec, c.a)
        r.fld[c.b] = r.fld.get(c.b, 0) + c.c
    elif c.kind == "mov":
        if c.b == "-":
            _mine(rec, c.a).up = None
            return
        if c.b not in rec or reach.inside(rec, c.a, c.b):
            return
        _mine(rec, c.a).up = c.b
    elif c.kind == "cut":
        for name in reach.under(rec, c.a):
            del rec[name]
        del rec[c.a]
