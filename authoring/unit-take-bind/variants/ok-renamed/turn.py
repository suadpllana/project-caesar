from prog.deck import OWN, UNIT, at, blank, put
from prog.unit import find

from .pick import settle
from .show import out_all, out_one
from .step import cost, srcs


def settled(tbl, un, x):
    return at(tbl, un, x) is not None


def here(pgm, tbl, u, price, bag):
    if price:
        return
    for x in u.owns:
        if not settled(tbl, u.nm, x):
            bag.setdefault(x, []).append((OWN, u.nm))
    for x, from_ in u.als:
        if find(pgm, from_) is not None and not settled(tbl, u.nm, x):
            bag.setdefault(x, []).append((UNIT, from_))


def carried(pgm, tbl, u, price, bag):
    for s, want in u.pulls:
        for from_, hop in srcs(tbl, pgm, u, s):
            if want == "*":
                for x, b in out_all(tbl, pgm, from_):
                    if not settled(tbl, u.nm, x) and cost(hop, b[2]) == price:
                        bag.setdefault(x, []).append((b[0], b[1]))
            else:
                b = out_one(tbl, pgm, from_, want)
                if b is None or settled(tbl, u.nm, want):
                    continue
                if cost(hop, b[2]) == price:
                    bag.setdefault(want, []).append((b[0], b[1]))


def run(pgm):
    tbl = blank(pgm.units)
    price = 0
    while True:
        batch = []
        for u in pgm.units.values():
            bag = {}
            here(pgm, tbl, u, price, bag)
            carried(pgm, tbl, u, price, bag)
            for x, lot in bag.items():
                kind, tgt = settle(lot)
                batch.append((u.nm, x, kind, tgt))
        if not batch:
            return tbl
        for un, x, kind, tgt in batch:
            put(tbl, un, x, kind, tgt, price)
        price += 1
