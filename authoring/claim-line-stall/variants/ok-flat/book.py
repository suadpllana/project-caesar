"""Correct variant: claims in one flat map, with a per unit map of each job's scopes.

No counts by mode anywhere. A whole-unit ask is answered by looking at the scope sets of the
other jobs in that unit, which is a different structure from the reference's per job pair of
counts and a different cost, and has to produce the same trace.
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
        self.mode = {}
        self.byjob = {}
        self.spread = {}
        self.ask = {}
        self.queue = {}
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
    h.mode[(job, scope)] = mode
    h.bh.discard(job)
    h.byjob.setdefault(job, set()).add(scope)
    h.spread.setdefault(name.cut(scope)[0], {}).setdefault(job, {})[scope] = mode
    recheck(h, job)


def lose(h, job, scope):
    if (job, scope) not in h.mode:
        return False
    h.bh.discard(job)
    del h.mode[(job, scope)]
    mine = h.byjob.get(job)
    if mine is not None:
        mine.discard(scope)
        if not mine:
            del h.byjob[job]
    unit = name.cut(scope)[0]
    box = h.spread.get(unit, {}).get(job)
    if box is not None:
        box.pop(scope, None)
        if not box:
            del h.spread[unit][job]
            if not h.spread[unit]:
                del h.spread[unit]
    recheck(h, job)
    return True


def mine_here(h, job, unit):
    return h.spread.get(unit, {}).get(job, {})


def holds_over(h, job, scope):
    for one in mine_here(h, job, name.cut(scope)[0]):
        if overlap(one, scope):
            return True
    return False


def covered(h, job, scope, mode):
    for one, m in mine_here(h, job, name.cut(scope)[0]).items():
        if covers(one, scope) and atleast(m, mode):
            return True
    return False


def whoclash(h, job, scope, mode):
    out = set()
    for other, box in h.spread.get(name.cut(scope)[0], {}).items():
        if other == job:
            continue
        for one, m in box.items():
            if overlap(one, scope) and clash(mode, m):
                out.add(other)
                break
    return out


def anyclash(h, job, scope, mode):
    return bool(whoclash(h, job, scope, mode))


def clear(h, job):
    units = set()
    held = sorted(h.byjob.get(job, ()))
    for scope in held:
        units.add(name.cut(scope)[0])
        lose(h, job, scope)
    req = h.ask.pop(job, None)
    if req is not None:
        unit = name.cut(req[2])[0]
        units.add(unit)
        h.queue.get(unit, {}).pop(req[0], None)
    h.born.pop(job, None)
    h.bh.discard(job)
    return len(held), units, req is not None


def unfile(h, req):
    h.queue.get(name.cut(req[2])[0], {}).pop(req[0], None)
    if h.ask.get(req[1]) is req:
        del h.ask[req[1]]
    recheck(h, req[1])


def listing(h, unit):
    rows = []
    for job, box in h.spread.get(unit, {}).items():
        for scope, mode in box.items():
            rows.append((h.born[job], name.rank(scope), job, scope, mode))
    rows.sort()
    return ",".join("%s@%s=%s" % (r[2], r[3], r[4]) for r in rows)


def onunit(h, unit):
    return len(h.queue.get(unit, ()))
