# Correct variant "topdown": totals as plain 4-tuples (grants, requests, releases, beats).
from jl.read import Aud, Dig, Entry, Gap

ZERO = (0, 0, 0, 0)


def add(tot, kind, out):
    g, a, r, b = tot
    if kind == "beat":
        return g, a, r, b + 1
    grew = 1 if out in ("grant", "pass") else 0
    if kind == "acq":
        return g + grew, a + 1, r, b
    return g + grew, a, r + 1, b


def due(before, after, period):
    return after[0] != before[0] and after[0] % period == 0


def seen(aud):
    return aud.grants, aud.asks, aud.rels, aud.beats


def room(items, at):
    lim = None
    run = ZERO
    for rec in items[at + 1:]:
        if isinstance(rec, Entry):
            run = add(run, rec.kind, rec.out)
            continue
        marks = rec.marks if isinstance(rec, Gap) else [rec]
        for m in marks:
            if isinstance(m, Dig):
                bound = (m.grants - run[0], None, None, None)
            else:
                bound = tuple(x - y for x, y in zip(seen(m), run))
            lim = bound if lim is None else tuple(
                x if y is None else (y if x is None else min(x, y)) for x, y in zip(lim, bound))
        if isinstance(rec, Aud):
            break
    return lim
