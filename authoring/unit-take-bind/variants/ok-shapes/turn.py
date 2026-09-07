from prog.deck import OWN, UNIT, at, blank, put
from prog.unit import find

from .pick import settle
from .show import out_all, out_one
from .step import cost, srcs


def done(deck, un, x):
    return at(deck, un, x) is not None


def owned(prog, deck, u, rank, got):
    if rank:
        return
    for x in u.owns:
        if not done(deck, u.nm, x):
            got.setdefault(x, []).append((OWN, u.nm))
    for x, vn in u.als:
        if find(prog, vn) is not None and not done(deck, u.nm, x):
            got.setdefault(x, []).append((UNIT, vn))


def pulled(prog, deck, u, rank, got):
    for s, what in u.pulls:
        for vn, rs in srcs(deck, prog, u, s):
            if what == "*":
                for x, b in out_all(deck, prog, vn).items():
                    if not done(deck, u.nm, x) and cost(rs, b[2]) == rank:
                        got.setdefault(x, []).append((b[0], b[1]))
            else:
                b = out_one(deck, prog, vn, what)
                if b is None or done(deck, u.nm, what):
                    continue
                if cost(rs, b[2]) == rank:
                    got.setdefault(what, []).append((b[0], b[1]))


def run(prog):
    deck = blank(prog.units)
    rank = 0
    while True:
        fresh = []
        for u in prog.units.values():
            got = {}
            owned(prog, deck, u, rank, got)
            pulled(prog, deck, u, rank, got)
            for x, cands in got.items():
                kind, tgt = settle(cands)
                fresh.append((u.nm, x, kind, tgt))
        if not fresh:
            return deck
        for un, x, kind, tgt in fresh:
            put(deck, un, x, kind, tgt, rank)
        rank += 1
