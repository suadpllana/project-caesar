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
        self.ask = {}
        self.line = []
        self.born = {}
        self.nborn = 0
        self.nfile = 0


def wake(h, job):
    if job not in h.born:
        h.nborn += 1
        h.born[job] = h.nborn


def put(h, job, scope, mode):
    h.held.setdefault(job, {})[scope] = mode


def lose(h, job, scope):
    mine = h.held.get(job)
    if not mine or scope not in mine:
        return False
    del mine[scope]
    if not mine:
        del h.held[job]
    return True


def owns(h, job):
    return len(h.held.get(job) or ())


def holds_over(h, job, scope):
    for one in h.held.get(job) or ():
        if overlap(one, scope):
            return True
    return False


def covered(h, job, scope, mode):
    have = (h.held.get(job) or {}).get(name.cut(scope)[0])
    return have is not None and atleast(have, mode)


def cells(h, job, unit):
    out = []
    for one, mode in (h.held.get(job) or {}).items():
        u, c = name.cut(one)
        if c is not None and u == unit:
            out.append((one, mode))
    return out


def anyclash(h, job, scope, mode):
    for other, box in h.held.items():
        if other == job:
            continue
        for one, m in box.items():
            if overlap(one, scope) and clash(mode, m):
                return True
    return False


def whoclash(h, job, scope, mode):
    out = set()
    for other, box in h.held.items():
        if other == job:
            continue
        for one, m in box.items():
            if overlap(one, scope) and clash(mode, m):
                out.add(other)
                break
    return out


def clear(h, job):
    units = set()
    mine = list((h.held.get(job) or {}).items())
    for scope, _mode in mine:
        units.add(name.cut(scope)[0])
        lose(h, job, scope)
    req = h.ask.get(job)
    if req is not None:
        units.add(name.cut(req[2])[0])
        unfile(h, req)
    return len(mine), units, req is not None


def unfile(h, req):
    if req in h.line:
        h.line.remove(req)
    if h.ask.get(req[1]) is req:
        del h.ask[req[1]]


def listing(h, unit):
    rows = []
    for job, box in h.held.items():
        for scope, mode in box.items():
            if overlap(scope, unit):
                rows.append((h.born[job], name.rank(scope), job, scope, mode))
    rows.sort()
    return ",".join("%s@%s=%s" % (r[2], r[3], r[4]) for r in rows)


def onunit(h, unit):
    return len([r for r in h.line if overlap(r[2], unit)])
