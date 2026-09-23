from scn import rd


def usable(ch):
    return ch.enc == "d"


def classify(cond, dic):
    """How the chunk's dictionary settles `cond` for a row drawn from it:
    'drop' if no entry satisfies it (every such row fails), 'all' if every
    entry satisfies it (every non-null such row passes), else 'mixed'."""
    good = 0
    for v in dic:
        if rd.sat(cond, v):
            good += 1
    if good == 0:
        return "drop"
    if good == len(dic):
        return "all"
    return "mixed"
