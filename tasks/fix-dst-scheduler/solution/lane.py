from . import due, gate, rec, zt


class State:
    def __init__(self, jobs, led, horizon):
        self.jobs = jobs
        self.led = led
        self.horizon = horizon
        self.evs = []
        self.busy = None
        self.done = None
        self.pend = {}
        self.idx = {}
        self.nxt = {}

    @classmethod
    def fresh(cls, plan):
        st = cls(plan.jobs, gate.Ledger(), plan.horizon)
        for j in plan.jobs:
            st.pend[j.jid] = None
            st.idx[j.jid] = 0
            st.nxt[j.jid] = due.nom_at(j, 0, None)
        return st

    def part(self, jobs):
        st = State(jobs, self.led.copy(), self.horizon)
        for j in jobs:
            st.pend[j.jid] = self.pend[j.jid]
            st.idx[j.jid] = self.idx[j.jid]
            st.nxt[j.jid] = self.nxt[j.jid]
        return st

    def held(self, job):
        if self.pend[job.jid] is not None:
            return True
        return self.busy is not None and self.busy.job is job

    def bump(self, job, prev):
        if job.mode == "clock":
            self.nxt[job.jid] = due.nom_at(job, self.idx[job.jid], None)
        elif prev is None:
            self.nxt[job.jid] = None
        else:
            self.nxt[job.jid] = due.nom_at(job, self.idx[job.jid], prev)

    def log(self, kind, job, k, t):
        self.evs.append(rec.Ev(kind, job, k, t))


def marks(st, cur):
    out = []
    if st.busy is not None:
        out.append(st.done)
    for j in st.jobs:
        n = st.nxt[j.jid]
        if n is not None:
            out.append(n)
        o = st.pend[j.jid]
        if o is None:
            continue
        out.append(o.dead)
        if st.busy is None and not st.led.room(j, cur):
            out.append(zt.next_day(j.pool.zone, cur))
    return [t for t in out if t > cur]


def finish(st, t):
    if st.busy is not None and st.done == t:
        st.log("end", st.busy.job, st.busy.k, t)
        st.busy = None
        st.done = None


def arrive(st, t):
    for j in st.jobs:
        while st.nxt[j.jid] is not None and st.nxt[j.jid] <= t:
            k = st.idx[j.jid]
            if st.held(j):
                st.log("skip", j, k, t)
                st.idx[j.jid] = k + 1
                st.bump(j, None)
            else:
                o = rec.Occ(j, k, st.nxt[j.jid])
                o.dead = gate.dead_at(j, o.nom)
                st.pend[j.jid] = o
                st.idx[j.jid] = k + 1
                st.bump(j, None)


def expire(st, t):
    for j in st.jobs:
        o = st.pend[j.jid]
        if o is not None and o.dead <= t:
            st.log("drop", j, o.k, o.dead)
            st.pend[j.jid] = None
            st.bump(j, o.dead)


def reserved(st, job, t):
    above = [h for h in st.jobs if h.prio < job.prio]
    if not above:
        return False
    sub = st.part(above)
    until = t + job.dur
    launch(sub, t)
    cur = t
    while not any(e.kind == "start" for e in sub.evs):
        cands = marks(sub, cur)
        if not cands:
            break
        cur = min(cands)
        if cur >= until:
            break
        step(sub, cur)
    return any(e.kind == "start" for e in sub.evs)


def launch(st, t):
    if st.busy is not None:
        return
    for j in st.jobs:
        o = st.pend[j.jid]
        if o is None:
            continue
        if not st.led.room(j, t):
            continue
        if reserved(st, j, t):
            continue
        st.log("start", j, o.k, t)
        st.led.take(j, t)
        st.pend[j.jid] = None
        st.busy = o
        st.done = t + j.dur
        st.bump(j, t)
        return


def step(st, t):
    finish(st, t)
    arrive(st, t)
    expire(st, t)
    launch(st, t)


def run(plan):
    st = State.fresh(plan)
    cur = -1
    while True:
        cands = marks(st, cur)
        if not cands:
            break
        t = min(cands)
        if t >= st.horizon:
            break
        step(st, t)
        cur = t
    return st.evs
