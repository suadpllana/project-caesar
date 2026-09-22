from collections import namedtuple

from jl.read import Aud, Gap

Tot = namedtuple("Tot", "grants asks rels beats")
ZERO = Tot(0, 0, 0, 0)


def add(tot, kind, out):
    g, a, r, b = tot
    if kind == "acq":
        return Tot(g + (out == "grant"), a + 1, r, b)
    if kind == "rel":
        return Tot(g, a, r + 1, b)
    return Tot(g, a, r, b + 1)


def due(before, after, period):
    return after.grants > before.grants and after.grants % period == 0


def seen(aud):
    return Tot(aud.grants, aud.asks, aud.rels, aud.beats)


def room(items, at):
    for rec in items[at + 1:]:
        if isinstance(rec, Aud):
            return seen(rec)
        if isinstance(rec, Gap):
            for m in rec.marks:
                if isinstance(m, Aud):
                    return seen(m)
    return None
