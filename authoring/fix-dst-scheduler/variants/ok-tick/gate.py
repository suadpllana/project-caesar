from . import zt

SPANS = {}


def build(job, upto):
    rows = []
    t = 0
    guard = 0
    while t < upto + 2880 and guard < 20000:
        guard += 1
        if admits(job, t):
            end = t
            while admits(job, end):
                end = hop(job, end)
            rows.append((t, end))
            t = end
        else:
            t = hop(job, t)
    return rows


def hop(job, t):
    z = job.zone
    o = zt.off(z, t)
    val = t + o
    d = val % 1440
    if d < job.opn:
        val += job.opn - d
    elif d < job.shut:
        val += job.shut - d
    else:
        val += 1440 - d + job.opn
    cand = val - o
    e = zt.edge(z, t)
    if e is not None and e < cand:
        return e
    return cand


def admits(job, t):
    d = zt.tod(job.zone, t)
    return job.opn <= d < job.shut


def spans(job, upto):
    key = (job.jid, upto)
    if key not in SPANS:
        SPANS[key] = build(job, upto)
    return SPANS[key]


def dead_at(job, n, upto):
    for lo, hi in spans(job, upto):
        if lo <= n < hi:
            return hi
    return n


class Ledger:
    def __init__(self):
        self.tally = {}

    def copy(self):
        c = Ledger()
        c.tally = dict(self.tally)
        return c

    def cell(self, job, t):
        return (job.pool.name, zt.day(job.pool.zone, t))

    def room(self, job, t):
        return self.tally.get(self.cell(job, t), 0) < job.pool.cap

    def take(self, job, t):
        c = self.cell(job, t)
        self.tally[c] = self.tally.get(c, 0) + 1
