# Correct variant "packed": totals as tuples; the slack of a span read from a table of
# totals-so-far built once per journal.
from jl.read import Aud, Dig, Entry, Gap

ZERO = (0, 0, 0, 0)
KIND = {"acq": 1, "rel": 2, "beat": 3}


def add(tot, kind, out):
    t = list(tot)
    t[KIND[kind]] += 1
    if out == "grant" or out == "pass":
        t[0] += 1
    return tuple(t)


def due(before, after, period):
    return after[0] > before[0] and after[0] % period == 0


def seen(aud):
    return (aud.grants, aud.asks, aud.rels, aud.beats)


def room(items, at):
    known = ZERO
    cap = [None] * 4
    for rec in items[at + 1:]:
        if isinstance(rec, Entry):
            known = add(known, rec.kind, rec.out)
            continue
        for m in ([rec] if not isinstance(rec, Gap) else list(rec.marks)):
            if isinstance(m, Dig):
                pairs = [(0, m.grants)]
            else:
                pairs = list(enumerate(seen(m)))
            for k, v in pairs:
                c = v - known[k]
                cap[k] = c if cap[k] is None else min(cap[k], c)
        if isinstance(rec, Aud):
            break
    return tuple(cap)
