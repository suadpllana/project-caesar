from . import zt


def admits(job, t):
    d = zt.tod(job.zone, t)
    return job.opn <= d < job.shut


def shut_at(job, t):
    d = zt.tod(job.zone, t)
    if d < job.opn:
        return t + (job.opn - d)
    return t + (job.shut - d)


def dead_at(job, n):
    if not admits(job, n):
        return n
    return shut_at(job, n)


class Ledger:
    def __init__(self):
        self.used = {}

    def slot(self, job, t):
        return (job.pool.name, zt.day(job.zone, t))

    def room(self, job, t):
        return self.used.get(self.slot(job, t), 0) < job.pool.cap

    def take(self, job, t):
        s = self.slot(job, t)
        self.used[s] = self.used.get(s, 0) + 1
