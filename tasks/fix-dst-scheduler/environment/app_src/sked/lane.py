from . import due, gate, rec


def build(plan):
    out = {}
    for j in plan.jobs:
        line = []
        prev = None
        k = 0
        while True:
            n = due.nom_at(j, k, prev)
            if n >= plan.horizon:
                break
            o = rec.Occ(j, k, n)
            o.dead = gate.dead_at(j, n)
            line.append(o)
            prev = n
            k += 1
        out[j.jid] = line
    return out


class State:
    def __init__(self, plan):
        self.plan = plan
        self.led = gate.Ledger()
        self.evs = []
        self.busy = None
        self.done = None
        self.pend = {}
        self.line = build(plan)
        self.at = {}
        for j in plan.jobs:
            self.pend[j.jid] = None
            self.at[j.jid] = 0

    def ahead(self, job):
        line = self.line[job.jid]
        i = self.at[job.jid]
        if i >= len(line):
            return None
        return line[i].nom

    def held(self, job):
        if self.pend[job.jid] is not None:
            return True
        return self.busy is not None and self.busy.job is job

    def log(self, kind, job, k, t):
        self.evs.append(rec.Ev(kind, job, k, t))


def marks(st, cur):
    out = []
    if st.busy is not None:
        out.append(st.done)
    for j in st.plan.jobs:
        n = st.ahead(j)
        if n is not None:
            out.append(n)
        o = st.pend[j.jid]
        if o is not None:
            out.append(o.dead)
    return [t for t in out if t > cur]


def finish(st, t):
    if st.busy is not None and st.done == t:
        st.log("end", st.busy.job, st.busy.k, t)
        st.led.take(st.busy.job, t)
        st.busy = None
        st.done = None


def arrive(st, t):
    for j in st.plan.jobs:
        while True:
            n = st.ahead(j)
            if n is None or n > t:
                break
            o = st.line[j.jid][st.at[j.jid]]
            st.at[j.jid] += 1
            if st.held(j):
                st.log("skip", j, o.k, t)
            else:
                st.pend[j.jid] = o


def expire(st, t):
    for j in st.plan.jobs:
        o = st.pend[j.jid]
        if o is not None and o.dead <= t:
            st.log("drop", j, o.k, o.dead)
            st.pend[j.jid] = None


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
        st.pend[j.jid] = None
        st.busy = o
        st.done = t + j.dur
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
