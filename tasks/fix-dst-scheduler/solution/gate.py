from . import zt


def admits(job, t):
    d = zt.tod(job.zone, t)
    return job.opn <= d < job.shut


def step_on(job, t):
    z = job.zone
    o = zt.off(z, t)
    val = t + o
    d = val % 1440
    if d < job.opn:
        nxt = val + (job.opn - d)
    elif d < job.shut:
        nxt = val + (job.shut - d)
    else:
        nxt = val + (1440 - d) + job.opn
    cand = nxt - o
    e = zt.edge(z, t)
    if e is not None and e < cand:
        return e
    return cand


def shut_at(job, t):
    while admits(job, t):
        t = step_on(job, t)
    return t


def dead_at(job, n):
    if not admits(job, n):
        return n
    return shut_at(job, n + 1)


class Ledger:
    def __init__(self):
        self.used = {}

    def copy(self):
        other = Ledger()
        other.used = dict(self.used)
        return other

    def slot(self, job, t):
        return (job.pool.name, zt.day(job.pool.zone, t))

    def room(self, job, t):
        return self.used.get(self.slot(job, t), 0) < job.pool.cap

    def take(self, job, t):
        s = self.slot(job, t)
        self.used[s] = self.used.get(s, 0) + 1
