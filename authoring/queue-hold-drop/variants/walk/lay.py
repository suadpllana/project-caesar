from . import reach
from .store import Rec


def one(rec, c):
    kind = c.kind
    if kind == "set" or kind == "add":
        r = rec.get(c.a)
        if r is None:
            return
        was = r.fld.get(c.b, 0)
        r.fld[c.b] = c.c if kind == "set" else was + c.c
        return
    up = None if c.b == "-" else c.b
    if kind == "new":
        if c.a not in rec and (up is None or up in rec):
            rec[c.a] = Rec(up)
        return
    if c.a not in rec:
        return
    if kind == "mov":
        if up is not None and (up not in rec or reach.inside(rec, c.a, up)):
            return
        rec[c.a].up = up
        return
    if kind == "cut":
        for name in reach.under(rec, c.a):
            rec.pop(name, None)
        rec.pop(c.a, None)
