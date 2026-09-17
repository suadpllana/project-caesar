from . import due, gate, rec


def expand(plan):
    out = []
    for j in plan.jobs:
        prev = None
        k = 0
        while True:
            n = due.nom_at(j, k, prev)
            if n >= plan.horizon:
                break
            o = rec.Occ(j, k, n)
            o.dead = gate.dead_at(j, n)
            out.append(o)
            prev = n
            k += 1
    out.sort(key=lambda o: (o.nom, o.job.prio))
    return out


class Sweep:
    def __init__(self, plan):
        self.plan = plan
        self.led = gate.Ledger()
        self.evs = []
        self.free = 0
        self.tail = {}

    def log(self, kind, job, k, t):
        if t < self.plan.horizon:
            self.evs.append(rec.Ev(kind, job, k, t))

    def place(self, o):
        j = o.job
        if o.nom < self.tail.get(j.jid, 0):
            self.log("skip", j, o.k, o.nom)
            return
        if o.dead <= o.nom:
            self.log("drop", j, o.k, o.dead)
            return
        t = max(o.nom, self.free)
        if t >= o.dead or not self.led.room(j, t):
            self.log("drop", j, o.k, o.dead)
            return
        self.log("start", j, o.k, t)
        self.log("end", j, o.k, t + j.dur)
        self.led.take(j, t + j.dur)
        self.free = t + j.dur
        self.tail[j.jid] = t + j.dur


def run(plan):
    sw = Sweep(plan)
    for o in expand(plan):
        sw.place(o)
    return sw.evs
