# Loose-cap variant: a span capped by the next digest and audit alone, without taking
# off what the surviving entries before them add. Exact, and wider to search.
from collections import namedtuple

from jl.read import Aud, Dig, Entry, Gap

Tot = namedtuple("Tot", "grants asks rels beats")
ZERO = Tot(0, 0, 0, 0)


def add(tot, kind, out):
    g, a, r, b = tot
    if kind == "acq":
        return Tot(g + (out == "grant"), a + 1, r, b)
    if kind == "rel":
        return Tot(g + (out == "pass"), a, r + 1, b)   # a hand-off is a grant
    return Tot(g, a, r, b + 1)


def due(before, after, period):
    return after.grants > before.grants and after.grants % period == 0


def seen(aud):
    return Tot(aud.grants, aud.asks, aud.rels, aud.beats)


def room(items, at):
    """Caps on the totals when the span at `at` is left: every later audit and digest, less
    what the surviving entries before it are known to add. Stops at the first surviving
    audit, which every journal has at its end."""
    far = 1 << 30
    cap = [far, far, far, far]
    got = ZERO
    for rec in items[at + 1:]:
        if isinstance(rec, Entry):
            continue
        for m in (rec.marks if isinstance(rec, Gap) else (rec,)):
            if isinstance(m, Dig):
                cap[0] = min(cap[0], m.grants - got.grants)
            else:
                for k, v in enumerate(seen(m)):
                    cap[k] = min(cap[k], v - got[k])
        if isinstance(rec, Aud):
            break
    return Tot(*cap)
