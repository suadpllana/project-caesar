I'll start by reading the scheduler code and the plans.

Bash(ls -R sked plans && cat run_plan.py sked/*.py && cat plans/coast.txt plans/island.txt)

plans:
coast.txt
island.txt

sked:
__init__.py
check.py
due.py
emit.py
gate.py
lane.py
read.py
rec.py
zt.py
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sked import emit, lane, read


def main():
    plan = read.load(sys.argv[1])
    for ln in emit.lines(lane.run(plan)):
        print(ln)


main()
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
from . import zt


def nom_at(job, k, prev):
    if job.mode == "clock":
        return zt.at_local(job.zone, job.anchor) + k * job.step
    if k == 0:
        return job.anchor
    return prev + job.step
RANK = {"end": 0, "skip": 1, "drop": 2, "start": 3}


def key(e):
    return (e.t, RANK[e.kind], e.job.prio)


def lines(evs):
    return ["%s %s %d %d" % (e.kind, e.job.jid, e.k, e.t) for e in sorted(evs, key=key)]
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
from . import check, rec


def parse(text):
    p = rec.Plan()
    for raw in text.splitlines():
        f = raw.split()
        if not f:
            continue
        head = f[0]
        if head == "zone":
            p.zones[f[1]] = rec.Zon
… [clipped]
collapse
Thinking…
Found several spec violations: at_local mishandles gaps, clock jobs add steps in elapsed time instead of local time, follow jobs chain off nominal dues rather than attempt instants, deadlines ignore shifts, pool charging uses the wrong zone/timing, and the event loop misses day rollovers. Now I'll rewrite the four permitted files to fix these.

Bash({"command":"cat > sked/zt.py <<'EOF'\ndef segs(z):\n out = []\n lo = None\n o = z.base\n for at, no in z.shift…)

/bin/bash: line 527:   111 Killed                  python3 run_plan.py plans/coast.txt
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
/bin/bash: line 527:   111 Killed                  python3 run_plan.py plans/coast.txt
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
The coast plan hangs. Let me trace it.

Bash(timeout 5 python3 -c " import sys; sys.path.insert(0,'.') from sked import read, lane, gate, zt p = read.load(…)

Exit code 143
Terminated

[error] tool reported failure
collapse
Bash(timeout 5 python3 -u -c " import sys; sys.path.insert(0,'.') from sked import read, lane, gate, zt p = read.lo…)

Exit code 143
Terminated

[error] tool reported failure
collapse
Bash(timeout 5 python3 -u -c " import sys; sys.path.insert(0,'.') from sked import read, zt, due, gate p = read.loa…)

loaded
sweep 135
480
purge 60
270
rollup 150
600
1440

[stdout]
loaded
sweep 135
480
purge 60
270
rollup 150
600
1440
[metadata] {"noOutputExpected": false}
collapse
Bash(timeout 5 python3 -u -c " import sys; sys.path.insert(0,'.') from sked import read, gate import sked.lane as L…)

Exit code 143
Terminated

[error] tool reported failure
collapse
Bash(timeout 5 python3 -u -c " import sys; sys.path.insert(0,'.') print('start') from sked import read import sked.…)

start
imported
state
[135, 60, 150]
exit 0

[stdout]
start
imported
state
[135, 60, 150]
exit 0
[metadata] {"noOutputExpected": false}
collapse
Bash(timeout 5 python3 -u -c " import sys; sys.path.insert(0,'.') from sked import read import sked.lane as L p = r…)

t 60 [60, 135, 150]
a
e
l
t 120 [120, 135, 150, 1500]
a
e
l
t 135 [135, 150, 1500]
a
e
l
t 150 [150, 225, 1500, 1560]
a
e
l
t 225 [225, 600, 1440, 1500, 1560]
a
e
l
t 270 [270, 525, 1500, 1560]
a
e
l
t 525 [525, 1500, 1560]
exit 124

[stdout]
t 60 [60, 135, 150]
a
e
l
t 120 [120, 135, 150, 1500]
a
e
l
t 135 [135, 150, 1500]
a
e
l
t 150 [150, 225, 1500, 1560]
a
e
l
t 225 [225, 600, 1440, 1500, 1560]
a
e
l
t 270 [270, 525, 1500, 1560]
a
e
l
t 525 [525, 1500, 1560]
exit 124
[metadata] {"noOutputExpected": false}
collapse
Thinking…
I found the bug: a follow job's next due date is calculated from the last attempt, so occurrence k keeps resolving to the same instant until occurrence k-1 is actually attempted. I'll add tracking for which occurrence the last attempt belongs to.

Bash(python3 - <<'EOF' import re s = open('sked/lane.py').read() s = s.replace(""" prev = self.last[job.jid] if pre…)

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
[metadata] {"noOutputExpected": false}
collapse
Thinking…
I'll fix a potential ordering issue by precomputing and sorting clock dues by instant when backward-then-forward shifts are combined, then run a speed stress test.

Bash(python3 - <<'EOF' s = open('sked/lane.py').read() s = s.replace(""" self.last = {} for j in plan.jobs: self.pe…)

75ee34f263d28373fb51ef5a315f295a  -
4ac9e3e64db496bd6bdd667e60e5fc85  -
Traceback (most recent call last):
  File "/app/run_plan.py", line 15, in <module>
    main()
  File "/app/run_plan.py", line 10, in main
    plan = read.load(sys.argv[1])
           ^^^^^^^^^^^^^^^^^^^^^^
  File "/app/sked/read.py", line 33, in load
    return parse(fh.read())
           ^^^^^^^^^^^^^^^^
  File "/app/sked/read.py", line 28, in parse
    return check.plan(p)
           ^^^^^^^^^^^^^
  File "/app/sked/check.py", line 54, in plan
    jobs(p)
  File "/app/sked/check.py", line 33, in jobs
    bad("window span %s" % j.jid)
  File "/app/sked/check.py", line 2, in bad
    raise ValueError(what)
ValueError: window span j1
0

real	0m0.031s
user	0m0.020s
sys	0m0.008s

[stdout]
75ee34f263d28373fb51ef5a315f295a  -
4ac9e3e64db496bd6bdd667e60e5fc85  -
Traceback (most recent call last):
  File "/app/run_plan.py", line 15, in <module>
    main()
  File "/app/run_plan.py", line 10, in main
    plan = read.load(sys.argv[1])
           ^^^^^^^^^^^^^^^^^^^^^^
  File "/app/sked/read.py", line 33, in load
    return parse(fh.read())
           ^^^^^^^^^^^^^^^^
  File "/app/sked/read.py", line 28, in parse
    return check.plan(p)
           ^^^^^^^^^^^^^
  File "/app/sked/check.py", line 54, in plan
    jobs(p)
  File "/app/sked/check.py", line 33, in jobs
    bad("window span %s" % j.jid)
  File "/app/sked/check.py", line 2, in bad
    raise ValueError(what)
ValueError: window span j1
0

real	0m0.031s
user	0m0.020s
sys	0m0.008s
[metadata] {"noOutputExpected": false}
collapse
Bash(sed -i 's/clock 1 100$/clock 1 130/; s/job j1 a 1 p 5 0 1440/job j1 a 1 p 5 0 1300/; s/job j4 b 4 q 1 0 1440/j…)

Traceback (most recent call last):
  File "/app/run_plan.py", line 15, in <module>
    main()
  File "/app/run_plan.py", line 10, in main
    plan = read.load(sys.argv[1])
           ^^^^^^^^^^^^^^^^^^^^^^
  File "/app/sked/read.py", line 33, in load
    return parse(fh.read())
           ^^^^^^^^^^^^^^^^
  File "/app/sked/read.py", line 28, in parse
    return check.plan(p)
           ^^^^^^^^^^^^^
  File "/app/sked/check.py", line 54, in plan
    jobs(p)
  File "/app/sked/check.py", line 33, in jobs
    bad("window span %s" % j.jid)
  File "/app/sked/check.py", line 2, in bad
    raise ValueError(what)
ValueError: window span j3
0

real	0m0.035s
user	0m0.021s
sys	0m0.010s
Traceback (most recent call last):
  File "/app/run_plan.py", line 15, in <module>
    main()
  File "/app/run_plan.py", line 10, in main
    plan = read.load(sys.argv[1])
           ^^^^^^^^^^^^^^^^^^^^^^
  File "/app/sked/read.py", line 33, in load
    return parse(fh.read())
           ^^^^^^^^^^^^^^^^
  File "/app/sked/read.py", line 28, in parse
    return check.plan(p)
           ^^^^^^^^^^^^^
  File "/app/sked/check.py", line 54, in plan
    jobs(p)
  File "/app/sked/check.py", line 33, in jobs
    bad("window span %s" % j.jid)
  File "/app/sked/check.py", line 2, in bad
    raise ValueError(what)
ValueError: window span j3
ordered ok
same

[stdout]
Traceback (most recent call last):
  File "/app/run_plan.py", line 15, in <module>
    main()
  File "/app/run_plan.py", line 10, in main
    plan = read.load(sys.argv[1])
           ^^^^^^^^^^^^^^^^^^^^^^
  File "/app/sked/read.py", line 33, in load
    return parse(fh.read())
           ^^^^^^^^^^^^^^^^
  File "/app/sked/read.py", line 28, in parse
    return check.plan(p)
           ^^^^^^^^^^^^^
  File "/app/sked/check.py", line 54, in plan
    jobs(p)
  File "/app/sked/check.py", line 33, in jobs
    bad("window span %s" % j.jid)
  File "/app/sked/check.py", line 2, in bad
    raise ValueError(what)
ValueError: window span j3
0

real	0m0.035s
user	0m0.021s
sys	0m0.010s
Traceback (most recent call last):
  File "/app/run_plan.py", line 15, in <module>
    main()
  File "/app/run_plan.py", line 10, in main
    plan = read.load(sys.argv[1])
           ^^^^^^^^^^^^^^^^^^^^^^
  File "/app/sked/read.py", line 33, in load
    return parse(fh.read())
           ^^^^^^^^^^^^^^^^
  File "/app/sked/read.py", line 28, in parse
    return check.plan(p)
           ^^^^^^^^^^^^^
  File "/app/sked/check.py", line 54, in plan
    jobs(p)
  File "/app/sked/check.py", line 33, in jobs
    bad("window span %s" % j.jid)
  File "/app/sked/check.py", line 2, in bad
    raise ValueError(what)
ValueError: window span j3
ordered ok
same
[metadata] {"noOutputExpected": false}
collapse
Bash(sed -i 's/job j3 a 3 p 200 0 1400/job j3 a 3 p 200 100 1400/' /tmp/stress.txt time python3 run_plan.py /tmp/st…)

452710

real	0m3.931s
user	0m3.789s
sys	0m0.149s
ordered ok 452710

[stdout]
452710

real	0m3.931s
user	0m3.789s
sys	0m0.149s
ordered ok 452710
[metadata] {"noOutputExpected": false}
collapse
Fast enough. Last check: brute-force verify the zone helpers against the literal definitions.

Bash(python3 -c " import sys; sys.path.insert(0,'.') from sked import read, zt, gate p = read.load('/tmp/stress.txt…)

helpers ok

[stdout]
helpers ok
[metadata] {"noOutputExpected": false}
collapse
Done. The coast plan now prints `start sweep 1 1560`, the shift instant, instead of 1575, and the island plan's output checks out by hand against the spec.

**What was wrong**, and what I changed in the four permitted files:

- `sked/zt.py`: local-minute resolution took the earliest matching instant and, in a gap, computed a nonexistent instant. It now takes the latest exact hit, or the first instant whose local minute is past the wanted one.
- `sked/due.py`: clock jobs resolved only the anchor and then added the step in elapsed time. Each occurrence's local minute is now resolved separately, and a new helper produces a clock job's dues in the order they actually come due. Follow jobs now chain off the instant the previous occurrence was attempted.
- `sked/gate.py`: the drop deadline was a fixed distance from the due instant, ignoring shifts inside the window. It now walks the zone's shifts to find the first non-admitted instant. Pool charging was keyed on the job's zone. It now uses the pool's own zone. A new helper finds the next local-day boundary of a zone.
- `sked/lane.py`: pool cap was charged at run end rather than at start. Follow dues are computed at runtime from recorded attempts, tracked per occurrence so a pending occurrence does not spawn duplicates. The event loop now also wakes at pool day boundaries, so an occurrence blocked only by a full pool starts when the cap resets.

**Verification**: the zone helpers match brute-force definitions across every minute of a zone with four shifts including a back-then-forward pair. A stress plan with six jobs, steps as small as 1, and a horizon of 200000 minutes runs in about four seconds and produces monotonically ordered output, so the hidden set should fit the 600 second budget comfortably. The five untouched files were not modified.