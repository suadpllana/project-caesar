OWN = "own"
UNIT = "unit"
CLASH = "clash"


def blank(names):
    return {n: {} for n in names}


def at(deck, un, x):
    got = deck.get(un)
    if got is None:
        return None
    return got.get(x)


def row(deck, un):
    got = deck.get(un)
    if got is None:
        return {}
    return got


def put(deck, un, x, kind, tgt, rank):
    deck[un][x] = (kind, tgt, rank)
