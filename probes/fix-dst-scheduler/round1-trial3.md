I'll start by reading the scheduler code and the plans.

Bash(ls -R . | head -50 && for f in run_plan.py sked/*.py plans/*.txt; do echo "=== $f"; cat $f; done)

.:
plans
run_plan.py
sked

./plans:
coast.txt
island.txt

./sked:
__init__.py
check.py
due.py
emit.py
gate.py
lane.py
read.py
rec.py
zt.py
=== run_plan.py
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sked import emit, lane, read


def main():
    plan = read.load(sys.argv[1])
    for ln in emit.lines(lane.run(plan)):
        print(ln)


main()
=== sked/__init__.py
=== sked/check.py
def bad(what):
    raise ValueError(what)


def zones(plan):
    for z in plan.zones.values():
        last = None
        for at, _ in z.shifts:
            if at < 1:
                bad("shift at %d" % at)
            if last is not None and at <= last:
                bad("shift order %s" % z.name)
            last = at


def pools(plan):
    for p in plan.pools.values():
        if p.cap < 1:
            bad("cap %s" % p.name)


def jobs(plan):
    seen = set()
    for j in plan.jobs:
        if j.prio in seen:
            bad("priority %d" % j.prio)
        seen.add(j.prio)
        if j.mode not in ("clock", "follow"):
            bad("mode %s" % j.mode)
        if not 0 <= j.opn < j.shut <= 1440:
            bad("window %s" % j.jid)
        if j.shut - j.opn > 1320:
            bad("window span %s" % j.jid)
        if j.dur < 1:
            bad("duration %s" % j.jid)
        if j.step < 1:
            bad("step %s" % j.jid)
        if j.mode == "follow" and j.step <= j.dur:
            bad("follow step %s" % j.jid)
        if j.anchor < 0:
            bad("anchor %s" % j.jid)
        top = max([j.zone.base] + [o for _, o in j.zone.shifts])
        if j.anchor < top:
            bad("anchor before the epoch %s" % j.jid)


def plan(p):
    if p.horizon < 1:
        bad("horizon")
    if not p.jobs:
        bad("jobs")
    zones(p)
    pools(p)
    jobs(p)
    return p
=== sked/due.py
from . import zt


def nom_at(job, k, prev):
    if job.mode == "clock":
        return zt.at_local(job.zone, job.anchor) + k * job.step
    if k == 0:
        return job.anchor
    return prev + job.step
=== sked/emit.py
RANK = {"end": 0, "skip": 1, "drop": 2, "start": 3}


def key(e):
    return (e.t, RANK[e.kind], e.job.prio)


def lines(evs):
    return ["%s %s %d %d" % (e.kind, e.job.jid, e.k, e.t) for e in sorted(evs, key=key)]
=== sked/gate.py
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
=== sked/lane.py
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
=== sked/read.py
from . import check, rec


def parse(text):
    p = rec.Plan()
    for r
… [clipped]
collapse
Thinking…
Found several spec violations: at_local picks the wrong fold instant and mishandles gaps, clock mode applies the step offset after resolution instead of before, follow mode uses nominal times instead of attempt instants, deadlines miss shifts within the window, and the pool ledger charges the wrong zone at the wrong time. I'll now rewrite the four affected files to fix these.

Bash(cat > sked/zt.py <<'EOF' def segs(z): out = [] lo = None o = z.base for at, no in z.shifts: out.append((lo, at…)

start purge 0 60
end purge 0 120
start sweep 0 135
end sweep 0 225
start rollup 0 225
end rollup 0 270
drop rollup 1 600
drop rollup 2 900
drop rollup 3 1200
drop rollup 4 1500
start purge 1 1500
end purge 1 1560
start sweep 1 1560
end sweep 1 1650
start rollup 5 1800
end rollup 5 1845
drop rollup 6 2100
drop rollup 7 2400
drop rollup 8 2700
start purge 2 2940
end purge 2 3000
start sweep 2 3000
end sweep 2 3090
start rollup 9 3090
end rollup 9 3135
drop rollup 10 3420
drop rollup 11 3720
drop rollup 12 4020
---
start flush 0 60
end flush 0 150
start tally 0 540
end tally 0 740
start scan 0 740
skip scan 1 780
end scan 0 890
drop scan 2 960
drop scan 3 1140
drop scan 4 1320
drop scan 5 1500
start flush 1 1500
end flush 1 1590
drop scan 6 1680
drop scan 7 1860
start tally 1 1980
end tally 1 2180
start scan 8 2180
skip scan 9 2220
end scan 8 2330
drop scan 10 2400
drop scan 11 2580
drop scan 12 2760
start flush 2 2940
drop scan 13 3000
end flush 2 3030
drop scan 14 3180
drop scan 15 3360
start tally 2 3480
end tally 2 3680
start scan 16 3680
skip scan 17 3720
end scan 16 3830
drop scan 18 3900
drop scan 19 4080
drop scan 20 4260

[stdout]
start purge 0 60
end purge 0 120
start sweep 0 135
end sweep 0 225
start rollup 0 225
end rollup 0 270
drop rollup 1 600
drop rollup 2 900
drop rollup 3 1200
drop rollup 4 1500
start purge 1 1500
end purge 1 1560
start sweep 1 1560
end sweep 1 1650
start rollup 5 1800
end rollup 5 1845
drop rollup 6 2100
drop rollup 7 2400
drop rollup 8 2700
start purge 2 2940
end purge 2 3000
start sweep 2 3000
end sweep 2 3090
start rollup 9 3090
end rollup 9 3135
drop rollup 10 3420
drop rollup 11 3720
drop rollup 12 4020
---
start flush 0 60
end flush 0 150
start tally 0 540
end tally 0 740
start scan 0 740
skip scan 1 780
end scan 0 890
drop scan 2 960
drop scan 3 1140
drop scan 4 1320
drop scan 5 1500
start flush 1 1500
end flush 1 1590
drop scan 6 1680
drop scan 7 1860
start tally 1 1980
end tally 1 2180
start scan 8 2180
skip scan 9 2220
end scan 8 2330
drop scan 10 2400
drop scan 11 2580
drop scan 12 2760
start flush 2 2940
drop scan 13 3000
end flush 2 3030
drop scan 14 3180
drop scan 15 3360
start tally 2 3480
end tally 2 3680
start scan 16 3680
skip scan 17 3720
end scan 16 3830
drop scan 18 3900
drop scan 19 4080
drop scan 20 4260
[metadata] {"noOutputExpected": false}
collapse
Both plans now match the spec on the spots I hand-checked. A quick timing check on a long horizon:

Bash(sed 's/horizon 4320/horizon 2000000/' plans/island.txt > /tmp/big.txt && time python3 run_plan.py /tmp/big.txt…)

18053

real	0m0.138s
user	0m0.119s
sys	0m0.017s

[stdout]
18053

real	0m0.138s
user	0m0.119s
sys	0m0.017s
[metadata] {"noOutputExpected": false}
collapse
Done. `start sweep 1 1560` now prints on the second morning of the coast plan, and both plans run in well under a second even at a horizon 500 times longer.

**What was wrong**, and what I changed in the four permitted files:

- **`sked/zt.py`**: `at_local` picked the earliest of two folded instants instead of the latest, and for a local minute that never happens it returned an instant an hour late. It now takes the latest hit, and for a gap returns the shift instant, which is the first instant whose local minute is past the wanted one.
- **`sked/due.py`**: clock mode resolved the anchor and then added `k * step` in elapsed minutes, so shift days were the wrong length. It now resolves `anchor + k * step` as a local minute. Follow mode's occurrence 0 was treated as an instant without resolution, and later ones chained off nominal times. It now resolves occurrence 0 and chains off the instant the previous occurrence was attempted.
- **`sked/gate.py`**: the deadline was a fixed distance from the due instant. It now walks the zone's shifts, returning either the instant the time of day reaches the closing or a shift instant that lands outside the window, whichever comes first. The pool ledger keyed on the job's zone. It now keys on the pool's own zone.
- **`sked/lane.py`**: occurrences were all built up front, which cannot work for follow jobs. Due instants are now generated lazily per job, and a start or drop records the attempt instant so the next follow occurrence is placed from it. The pool charge moved from run end to run start, and drops are logged at the instant they fall.

Hand-checked details on the two plans: the skipped scan occurrence in the island plan takes precedence over what would otherwise be a drop, the coast rollup waits on a full pool and drops at the window close, and the pool day for the 1800 rollup start is computed in the pool's zone after the shift.