from prog.deck import OWN, UNIT, blank, put
from prog.unit import find

from .pick import settle
from .show import out_all, out_one
from .step import cost, srcs


def once(prog, deck):
    nxt = blank(prog.units)
    for u in prog.units.values():
        got = {}
        for x in u.owns:
            got.setdefault(x, []).append((OWN, u.nm, 0))
        for x, vn in u.als:
            if find(prog, vn) is not None:
                got.setdefault(x, []).append((UNIT, vn, 0))
        for s, what in u.pulls:
            for vn, rs in srcs(deck, prog, u, s):
                if what == "*":
                    for x, b in out_all(deck, prog, vn):
                        got.setdefault(x, []).append((b[0], b[1], cost(rs, b[2])))
                else:
                    b = out_one(deck, prog, vn, what)
                    if b is not None:
                        got.setdefault(what, []).append((b[0], b[1], cost(rs, b[2])))
        for x, cands in got.items():
            low = min(c[2] for c in cands)
            kind, tgt = settle([(c[0], c[1]) for c in cands if c[2] == low])
            put(nxt, u.nm, x, kind, tgt, low)
    return nxt


def run(prog):
    deck = blank(prog.units)
    while True:
        nxt = once(prog, deck)
        if nxt == deck:
            return deck
        deck = nxt
