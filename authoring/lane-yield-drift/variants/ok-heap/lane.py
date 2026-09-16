import heapq

from . import due, gate, rec, zt


class Board:
    def __init__(self, plan):
        self.plan = plan
        self.led = gate.Ledger()
        self.evs = []
        self.wake = []
        self.busy = None
        self.ends = None
        self.wait = {}
        self.seq = {}
        self.due = {}
        for j in plan.jobs:
            self.wait[j.jid] = None
            self.seq[j.jid] = 0
            n = due.nom_at(j, 0, None)
            self.due[j.jid] = n
            self.set(n)

    def set(self, t):
        if t is not None and t < self.plan.horizon:
            heapq.heappush(self.wake, t)

    def add(self, kind, job, k, t):
        self.evs.append(rec.Ev(kind, job, k, t))

    def taken(self, job):
        if self.wait[job.jid] is not None:
            return True
        return self.busy is not None and self.busy.job is job

    def tried(self, job, t):
        if job.mode == "follow":
            n = due.nom_at(job, self.seq[job.jid], t)
            self.due[job.jid] = n
            self.set(n)


def closed(b, t):
    if b.busy is not None and b.ends == t:
        b.add("end", b.busy.job, b.busy.k, t)
        b.busy = None
        b.ends = None


def opened(b, t):
    for j in b.plan.jobs:
        while b.due[j.jid] is not None and b.due[j.jid] <= t:
            k = b.seq[j.jid]
            nom = b.due[j.jid]
            busy = b.taken(j)
            b.seq[j.jid] = k + 1
            if busy:
                b.add("skip", j, k, t)
            else:
                o = rec.Occ(j, k, nom)
                o.dead = gate.dead_at(j, nom)
                b.wait[j.jid] = o
                b.set(o.dead)
            if j.mode == "clock":
                b.due[j.jid] = due.nom_at(j, b.seq[j.jid], None)
                b.set(b.due[j.jid])
            else:
                b.due[j.jid] = None
                break


def lapsed(b, t):
    for j in b.plan.jobs:
        o = b.wait[j.jid]
        if o is not None and o.dead <= t:
            b.add("drop", j, o.k, o.dead)
            b.wait[j.jid] = None
            b.tried(j, o.dead)


def taken_up(b, t):
    if b.busy is not None:
        return
    for j in b.plan.jobs:
        o = b.wait[j.jid]
        if o is None or not b.led.room(j, t):
            continue
        b.add("start", j, o.k, t)
        b.led.take(j, t)
        b.wait[j.jid] = None
        b.busy = o
        b.ends = t + j.dur
        b.set(b.ends)
        b.tried(j, t)
        return
    for j in b.plan.jobs:
        if b.wait[j.jid] is not None:
            b.set(zt.next_day(j.pool.zone, t))


def run(plan):
    b = Board(plan)
    last = -1
    while b.wake:
        t = heapq.heappop(b.wake)
        if t <= last or t >= plan.horizon:
            continue
        last = t
        closed(b, t)
        opened(b, t)
        lapsed(b, t)
        taken_up(b, t)
    return b.evs
