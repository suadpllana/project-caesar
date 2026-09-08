from mrg.lay import split
from mrg.tree import Tr


def parse(lines):
    base = Tr()
    top = 0
    rounds = []
    lo, ro = [], []
    for raw in lines:
        w = raw.split()
        if not w:
            continue
        if w[0] in ("d", "f"):
            par, nm = split(w[2])
            pk = base.at(par)
            base.put(w[1], w[0], pk, nm, w[3] if w[0] == "f" else None)
            top = max(top, int(w[1]))
        elif w[0] == "sync":
            rounds.append((lo, ro))
            lo, ro = [], []
        elif w[0] == "L":
            lo.append(tuple(w[1:]))
        elif w[0] == "R":
            ro.append(tuple(w[1:]))
    if lo or ro:
        rounds.append((lo, ro))
    return base, top + 1, rounds
