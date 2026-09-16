#!/bin/bash
# cheat: rule-amb-early
# a repeated local minute resolves to the earlier instant
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
    lows = []
    for lo, hi, o in segs(z):
        t = val - o
        if lo is not None and t < lo:
            continue
        if hi is not None and t >= hi:
            continue
        lows.append(t)
    if lows:
        return min(lows)
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
PYEOF
