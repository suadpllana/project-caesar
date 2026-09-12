"""Correct variant: claims kept per scope, with a per unit set of the cell scopes in use.

The reference reaches a unit's cell claims through per job counts by mode; this reaches them
through the set of cell scopes the unit has claims on and then through the per scope map. The
line lives in line.py as two sequences rather than one, so nothing here knows about it.
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
        self.at = {}
        self.byjob = {}
        self.filled = {}
        self.ask = {}
        self.lifts = {}
        self.plain = {}
        self.byunit = {}
        self.bh = set()
        self.born = {}
        self.nborn = 0
        self.nfile = 0


def owns(h, job):
    return len(h.byjob.get(job, ()))


def recheck(h, job):
    if job in h.ask and h.byjob.get(job):
        h.bh.add(job)
    else:
        h.bh.discard(job)


def wake(h, job):
    if job not in h.born:
        h.nborn += 1
        h.born[job] = h.nborn


def rest(h, job):
    if not owns(h, job) and job not in h.ask:
        h.born.pop(job, None)


def put(h, job, scope, mode):
    h.at.setdefault(scope, {})[job] = mode
    h.byjob.setdefault(job, {})[scope] = mode
    unit, cell = name.cut(scope)
    if cell is not None:
        h.filled.setdefault(unit, set()).add(scope)
    recheck(h, job)


def lose(h, job, scope):
    mine = h.byjob.get(job)
    if not mine or scope not in mine:
        return False
    del mine[scope]
    if not mine:
        del h.byjob[job]
    box = h.at.get(scope)
    if box is not None:
        box.pop(job, None)
        if not box:
            del h.at[scope]
            unit, cell = name.cut(scope)
            if cell is not None:
                here = h.filled.get(unit)
                if here is not None:
                    here.discard(scope)
                    if not here:
                        del h.filled[unit]
    recheck(h, job)
    return True


def scopes_over(h, scope):
    unit, cell = name.cut(scope)
    out = [unit]
    if cell is None:
        out.extend(sorted(h.filled.get(unit, ())))
    else:
        out.append(scope)
    return out


def holds_over(h, job, scope):
    mine = h.byjob.get(job)
    if not mine:
        return False
    unit, cell = name.cut(scope)
    if unit in mine:
        return True
    if cell is not None:
        return scope in mine
    return any(name.cut(one)[0] == unit for one in mine)


def covered(h, job, scope, mode):
    mine = h.byjob.get(job) or {}
    for one, m in mine.items():
        if covers(one, scope) and atleast(m, mode):
            return True
    return False


def whoclash(h, job, scope, mode):
    out = set()
    for one in scopes_over(h, scope):
        for other, m in h.at.get(one, {}).items():
            if other != job and clash(mode, m):
                out.add(other)
    return out


def anyclash(h, job, scope, mode):
    for one in scopes_over(h, scope):
        for other, m in h.at.get(one, {}).items():
            if other != job and clash(mode, m):
                return True
    return False


def clear(h, job):
    units = set()
    held = sorted(h.byjob.get(job, ()))
    for scope in held:
        units.add(name.cut(scope)[0])
        lose(h, job, scope)
    req = h.ask.get(job)
    if req is not None:
        units.add(name.cut(req[2])[0])
        unfile(h, req)
    h.born.pop(job, None)
    h.bh.discard(job)
    return len(held), units, req is not None


def unfile(h, req):
    fid = req[0]
    h.lifts.pop(fid, None)
    h.plain.pop(fid, None)
    h.byunit.get(name.cut(req[2])[0], {}).pop(fid, None)
    if h.ask.get(req[1]) is req:
        del h.ask[req[1]]
    recheck(h, req[1])


def listing(h, unit):
    rows = []
    for one in [unit] + sorted(h.filled.get(unit, ())):
        for job, mode in h.at.get(one, {}).items():
            rows.append((h.born[job], name.rank(one), job, one, mode))
    rows.sort()
    return ",".join("%s@%s=%s" % (r[2], r[3], r[4]) for r in rows)


def onunit(h, unit):
    return len(h.byunit.get(unit, ()))
