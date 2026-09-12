"""The claim book: the scope and mode arithmetic, and what every job holds.

A unit covers itself and every cell of it; a cell covers only itself. Two scopes overlap when
either covers the other, and claims held by different jobs conflict when their scopes overlap
and at least one of them is a write. Every overlap is therefore inside one unit, which is why
claims are indexed by unit: the jobs holding the unit itself, the jobs holding each cell of
it, and per job a pair of counts of the cell claims it holds there by mode. The counts are
what make a whole-unit ask answerable without walking the unit's cells.

`bh` is kept alongside: the jobs that hold a claim and also have an ask waiting. Every loop of
jobs held up only by one another contains one of them, so it is the seed set for the stall
search and has to be maintained rather than recomputed.
"""
from hold import name


def covers(a, b):
    if a == b:
        return True
    ua, ca = name.cut(a)
    ub, cb = name.cut(b)
    return ca is None and cb is not None and ua == ub


def overlap(a, b):
    return covers(a, b) or covers(b, a)


def clash(m, n):
    return m == "w" or n == "w"


def atleast(have, want):
    return have == "w" or want == "r"


def strongest(*modes):
    return "w" if "w" in modes else "r"


class Hold:
    def __init__(self):
        self.out = []
        self.held = {}
        self.own = {}
        self.cell = {}
        self.tally = {}
        self.tot = {}
        self.ask = {}
        self.line = {}
        self.byunit = {}
        self.bh = set()
        self.born = {}
        self.nborn = 0
        self.nfile = 0


def wake(h, job):
    if job not in h.born:
        h.nborn += 1
        h.born[job] = h.nborn


def rest(h, job):
    if not h.held.get(job) and job not in h.ask:
        h.held.pop(job, None)
        h.born.pop(job, None)
        h.bh.discard(job)


def recheck(h, job):
    if job in h.ask and h.held.get(job):
        h.bh.add(job)
    else:
        h.bh.discard(job)


def _bump(box, job, mode, by):
    pair = box.setdefault(job, [0, 0])
    pair[0 if mode == "r" else 1] += by
    if not pair[0] and not pair[1]:
        del box[job]


def put(h, job, scope, mode):
    u, c = name.cut(scope)
    mine = h.held.setdefault(job, {})
    old = mine.get(scope)
    if old == mode:
        return
    mine[scope] = mode
    if c is None:
        h.own.setdefault(u, {})[job] = mode
        return
    h.cell.setdefault(u, {}).setdefault(scope, {})[job] = mode
    tal = h.tally.setdefault(u, {})
    tot = h.tot.setdefault(u, [0, 0])
    if old is not None:
        _bump(tal, job, old, -1)
        tot[0 if old == "r" else 1] -= 1
    _bump(tal, job, mode, 1)
    tot[0 if mode == "r" else 1] += 1


def lose(h, job, scope):
    mine = h.held.get(job)
    if not mine or scope not in mine:
        return False
    mode = mine.pop(scope)
    u, c = name.cut(scope)
    if c is None:
        by = h.own.get(u)
        if by is not None:
            by.pop(job, None)
            if not by:
                del h.own[u]
        return True
    by = h.cell.get(u, {}).get(scope)
    if by is not None:
        by.pop(job, None)
        if not by:
            del h.cell[u][scope]
            if not h.cell[u]:
                del h.cell[u]
    _bump(h.tally.get(u, {}), job, mode, -1)
    tot = h.tot.get(u)
    if tot is not None:
        tot[0 if mode == "r" else 1] -= 1
    return True


def holds_over(h, job, scope):
    for one in h.held.get(job) or ():
        if overlap(one, scope):
            return True
    return False


def covered(h, job, scope, mode):
    u, c = name.cut(scope)
    have = h.own.get(u, {}).get(job)
    if have is not None and atleast(have, mode):
        return True
    if c is None:
        return False
    have = h.cell.get(u, {}).get(scope, {}).get(job)
    return have is not None and atleast(have, mode)


def anyclash(h, job, scope, mode):
    for k, box in h.held.items():
        if k == job:
            continue
        for one, m in box.items():
            if overlap(one, scope) and clash(mode, m):
                return True
    return False


def whoclash(h, job, scope, mode):
    out = set()
    for k, box in h.held.items():
        if k == job:
            continue
        for one, m in box.items():
            if overlap(one, scope) and clash(mode, m):
                out.add(k)
                break
    return out


def clear(h, job):
    """Everything the job holds, plus its ask. Returns what was released and where."""
    units = set()
    mine = h.held.get(job) or {}
    n = len(mine)
    for scope in list(mine):
        units.add(name.cut(scope)[0])
        lose(h, job, scope)
    req = h.ask.get(job)
    if req is not None:
        units.add(name.cut(req[2])[0])
        unfile(h, req)
    h.held.pop(job, None)
    h.born.pop(job, None)
    h.bh.discard(job)
    return n, units, req is not None


def unfile(h, req):
    fid, job = req[0], req[1]
    h.line.pop(fid, None)
    h.ask.pop(job, None)
    box = h.byunit.get(name.cut(req[2])[0])
    if box is not None:
        box.pop(fid, None)


def listing(h, unit):
    rows = []
    for job, mode in h.own.get(unit, {}).items():
        rows.append((h.born[job], (0, 0), job, unit, mode))
    for scope, by in h.cell.get(unit, {}).items():
        for job, mode in by.items():
            rows.append((h.born[job], name.rank(scope), job, scope, mode))
    rows.sort()
    return ",".join("%s@%s=%s" % (r[2], r[3], r[4]) for r in rows)


def onunit(h, unit):
    return len(h.byunit.get(unit, ()))
