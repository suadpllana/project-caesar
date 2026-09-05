SING = 0
SCOPED = 1
TRANS = 2

FREE = ""


class Reg:
    def __init__(self, life, deps, facs, tag, wraps, shut):
        self.life = life
        self.deps = deps
        self.facs = facs
        self.tag = tag
        self.wraps = wraps
        self.shut = shut


def load(rows):
    t = {}
    for r in rows:
        t[r[0]] = Reg(r[1], list(r[2]), list(r[3]), r[4], r[5], r[6])
    return t


def reach(tbl, nm, seen=None):
    if seen is None:
        seen = set()
    if nm in seen or nm not in tbl:
        return seen
    seen.add(nm)
    for d in tbl[nm].deps:
        reach(tbl, d, seen)
    if tbl[nm].wraps:
        reach(tbl, tbl[nm].wraps, seen)
    return seen


def cycles(tbl, nm):
    seen = []
    stack = [(nm, ())]
    while stack:
        cur, path = stack.pop()
        if cur in path:
            return True
        if cur not in tbl:
            continue
        nxt = path + (cur,)
        for d in tbl[cur].deps:
            stack.append((d, nxt))
        if tbl[cur].wraps:
            stack.append((tbl[cur].wraps, nxt))
    del seen
    return False
