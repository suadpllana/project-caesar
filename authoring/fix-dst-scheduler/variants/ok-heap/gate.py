from . import zt


def admits(job, t):
    return job.opn <= zt.tod(job.zone, t) < job.shut


def bound(job, t):
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
    return e if e is not None and e < cand else cand


def dead_at(job, n):
    if not admits(job, n):
        return n
    t = n + 1
    while admits(job, t):
        t = bound(job, t)
    return t


class Ledger:
    def __init__(self):
        self.used = {}

    def copy(self):
        c = Ledger()
        c.used = dict(self.used)
        return c

    def key(self, job, t):
        return (job.pool.name, zt.day(job.pool.zone, t))

    def room(self, job, t):
        return self.used.get(self.key(job, t), 0) < job.pool.cap

    def take(self, job, t):
        k = self.key(job, t)
        self.used[k] = self.used.get(k, 0) + 1
