from . import due, gate, rec, zt


class State:
    def __init__(self, plan):
        self.plan = plan
        self.led = gate.Ledger()
        self.evs = []
        self.busy = None
        self.done = None
        self.pend = {}
        self.idx = {}
        self.nxt = {}
        for j in plan.jobs:
            self.pend[j.jid] = None
            self.idx[j.jid] = 0
            self.nxt[j.jid] = due.nom_at(j, 0, None)

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
    for j in st.plan.jobs:
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
    for j in st.plan.jobs:
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
    for j in st.plan.jobs:
        o = st.pend[j.jid]
        if o is not None and o.dead <= t:
            st.log("drop", j, o.k, o.dead)
            st.pend[j.jid] = None
            st.bump(j, o.dead)


def launch(st, t):
    if st.busy is not None:
        return
    for j in st.plan.jobs:
        o = st.pend[j.jid]
        if o is None:
            continue
        if not st.led.room(j, t):
            continue
        st.log("start", j, o.k, t)
        st.led.take(j, t)
        st.pend[j.jid] = None
        st.busy = o
        st.done = t + j.dur
        st.bump(j, t)
        return


def run(plan):
    st = State(plan)
    cur = -1
    while True:
        cands = marks(st, cur)
        if not cands:
            break
        t = min(cands)
        if t >= plan.horizon:
            break
        finish(st, t)
        arrive(st, t)
        expire(st, t)
        launch(st, t)
        cur = t
    return st.evs
