SING = 0
SCOPED = 1
TRANS = 2

class Reg:
    def __init__(self, life, deps, facs):
        self.life = life
        self.deps = deps
        self.facs = facs


def load(rows):
    t = {}
    for r in rows:
        t[r[0]] = Reg(r[1], list(r[2]), list(r[3]))
    return t


def reach(tbl, nm, seen=None):
    if seen is None:
        seen = set()
    if nm in seen:
        return seen
    seen.add(nm)
    for d in tbl[nm].deps:
        reach(tbl, d, seen)
    return seen
