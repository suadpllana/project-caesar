from . import reach
from .store import Rec


def one(rec, c):
    if c.kind == "new":
        if c.a in rec:
            return
        if c.b != "-" and c.b not in rec:
            return
        rec[c.a] = Rec(None if c.b == "-" else c.b)
    elif c.kind == "set":
        r = rec.get(c.a)
        if r is not None:
            r.fld[c.b] = c.c
    elif c.kind == "add":
        r = rec.get(c.a)
        if r is not None:
            r.fld[c.b] = r.fld.get(c.b, 0) + c.c
    elif c.kind == "mov":
        r = rec.get(c.a)
        if r is None:
            return
        p = None if c.b == "-" else c.b
        if p is not None and p not in rec:
            return
        if p is not None and reach.inside(rec, c.a, p):
            return
        r.up = p
    elif c.kind == "cut":
        if c.a not in rec:
            return
        for name in reach.under(rec, c.a):
            rec.pop(name, None)
        rec.pop(c.a, None)
