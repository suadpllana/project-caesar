MODES = ("IS", "IX", "S", "SIX", "X")

UP = {
    "IS": frozenset(("IS",)),
    "IX": frozenset(("IS", "IX")),
    "S": frozenset(("IS", "S")),
    "SIX": frozenset(("IS", "IX", "S", "SIX")),
    "X": frozenset(("IS", "IX", "S", "SIX", "X")),
}

BAD = {
    "IS": frozenset(("X",)),
    "IX": frozenset(("S", "SIX", "X")),
    "S": frozenset(("IX", "SIX", "X")),
    "SIX": frozenset(("IX", "S", "SIX", "X")),
    "X": frozenset(("IS", "IX", "S", "SIX", "X")),
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
    for m in MODES:
        up = UP[m]
        if a in up and b in up:
            return m
    return "X"
