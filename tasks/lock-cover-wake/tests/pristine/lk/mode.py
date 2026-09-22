UP = {
    "IS": frozenset(("IS",)),
    "IX": frozenset(("IS", "IX")),
    "S": frozenset(("IS", "S")),
    "SIX": frozenset(("IS", "IX", "SIX")),
    "X": frozenset(("IS", "IX", "SIX", "X")),
}

BAD = {
    "IS": frozenset(("X",)),
    "IX": frozenset(("S", "SIX", "X")),
    "S": frozenset(("IX", "SIX", "X")),
    "SIX": frozenset(("IX", "S", "SIX", "X")),
    "X": frozenset(("IS", "IX", "S", "SIX", "X")),
}

JOIN = {
    ("IS", "IS"): "IS", ("IS", "IX"): "IX", ("IS", "S"): "S",
    ("IS", "SIX"): "SIX", ("IS", "X"): "X",
    ("IX", "IX"): "IX", ("IX", "S"): "SIX", ("IX", "SIX"): "SIX", ("IX", "X"): "X",
    ("S", "S"): "S", ("S", "SIX"): "SIX", ("S", "X"): "X",
    ("SIX", "SIX"): "SIX", ("SIX", "X"): "X",
    ("X", "X"): "X",
}

NEED = {"S": "IS", "X": "IX"}


def ge(a, b):
    return b in UP[a]


def hits(a, b):
    return b in BAD[a]


def cover(a, b):
    if a is None:
        return b
    if b is None:
        return a
    got = JOIN.get((a, b))
    if got is None:
        got = JOIN.get((b, a))
    return got
