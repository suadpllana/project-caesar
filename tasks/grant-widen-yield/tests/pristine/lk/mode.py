ORD = ("IS", "IX", "S", "SIX", "X")

_OK = {
    ("IS", "IS"): True,
    ("IS", "IX"): True,
    ("IS", "S"): True,
    ("IS", "SIX"): True,
    ("IS", "X"): False,
    ("IX", "IX"): True,
    ("IX", "S"): False,
    ("IX", "SIX"): False,
    ("IX", "X"): False,
    ("S", "S"): True,
    ("S", "SIX"): False,
    ("S", "X"): False,
    ("SIX", "SIX"): False,
    ("SIX", "X"): False,
    ("X", "X"): False,
}

_SUP = {
    ("IS", "IS"): "IS",
    ("IS", "IX"): "IX",
    ("IS", "S"): "S",
    ("IS", "SIX"): "SIX",
    ("IS", "X"): "X",
    ("IX", "IX"): "IX",
    ("IX", "S"): "X",
    ("IX", "SIX"): "SIX",
    ("IX", "X"): "X",
    ("S", "S"): "S",
    ("S", "SIX"): "SIX",
    ("S", "X"): "X",
    ("SIX", "SIX"): "SIX",
    ("SIX", "X"): "X",
    ("X", "X"): "X",
}


def ok(a, b):
    pair = (a, b)
    return _OK[pair] if pair in _OK else _OK[(b, a)]


def sup(a, b):
    if a is None:
        return b
    if b is None:
        return a
    pair = (a, b)
    return _SUP[pair] if pair in _SUP else _SUP[(b, a)]


def cov(m):
    return "IS" if m in ("IS", "S", "SIX") else "IX"
