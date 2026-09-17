#!/bin/bash
# cheat: rule-reserve-stop-at-horizon
# the plan stops at the horizon, so a higher start past it holds nothing back
set -euo pipefail
mkdir -p /app/sked

cat > /app/sked/zt.py <<'PYEOF'
def segs(z):
    out = []
    lo = None
    o = z.base
    for at, no in z.shifts:
        out.append((lo, at, o))
        lo = at
        o = no
    out.append((lo, None, o))
    return out


def off(z, t):
    o = z.base
    for at, no in z.shifts:
        if at <= t:
            o = no
        else:
            break
    return o


def loc(z, t):
    return t + off(z, t)


def tod(z, t):
    return loc(z, t) % 1440


def day(z, t):
    return loc(z, t) // 1440


def edge(z, t):
    for at, _ in z.shifts:
        if at > t:
            return at
    return None


def at_local(z, val):
    hit = None
    for lo, hi, o in segs(z):
        t = val - o
        if lo is not None and t < lo:
            continue
        if hi is not None and t >= hi:
            continue
        if hit is None or t > hit:
            hit = t
    if hit is not None:
        return hit
    over = None
    for lo, hi, o in segs(z):
        t = val - o + 1
        if lo is not None and t < lo:
            t = lo
        if hi is not None and t >= hi:
            continue
        if over is None or t < over:
            over = t
    return over


def next_day(z, t):
    while True:
        want = (loc(z, t) // 1440 + 1) * 1440
        cand = want - off(z, t)
        e = edge(z, t)
        if e is not None and e <= cand:
            if day(z, e) != day(z, t):
                return e
            t = e
            continue
        return cand
PYEOF

cat > /app/sked/due.py <<'PYEOF'
from . import zt


def nom_at(job, k, prev):
    if job.mode == "clock":
        return zt.at_local(job.zone, job.anchor + k * job.step)
    if k == 0:
        return zt.at_local(job.zone, job.anchor)
    return prev + job.step
PYEOF

cat > /app/sked/gate.py <<'PYEOF'
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
PYEOF

cat > /app/sked/lane.py <<'PYEOF'
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
    until = min(t + job.dur, st.horizon)
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
PYEOF
