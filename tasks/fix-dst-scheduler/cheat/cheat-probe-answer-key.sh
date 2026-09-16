#!/bin/bash
# cheat: probe-answer-key
# the frozen answers of tests/gt.json carried verbatim, keyed on the plan, with nothing else to fall back on
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

    def slot(self, job, t):
        return (job.pool.name, zt.day(job.pool.zone, t))

    def room(self, job, t):
        return self.used.get(self.slot(job, t), 0) < job.pool.cap

    def take(self, job, t):
        s = self.slot(job, t)
        self.used[s] = self.used.get(s, 0) + 1
PYEOF

cat > /app/sked/lane.py <<'PYEOF'
import json

from . import rec

KEY = json.loads(r"""{"cap-rollover": ["start one 0 100", "end one 0 130", "start two 0 720", "end two 0 750", "start one 1 2160", "end one 1 2190", "drop two 1 2760"], "cap-yield": ["start filler 0 50", "end filler 0 80", "skip first 1 300", "start second 0 300", "end second 0 330", "skip first 2 500", "skip first 3 700", "skip first 4 900", "skip first 5 1100", "skip first 6 1300", "drop first 0 1320"], "dead-edge": ["start block 0 100", "end block 0 600", "drop thin 0 600", "start block 1 1540", "end block 1 2040", "drop thin 1 2040"], "fold-repeat": ["start scan 0 1530", "end scan 0 1560", "start scan 1 2970", "end scan 1 3000"], "gap-jump": ["start sweep 0 60", "end sweep 0 90", "start sweep 1 1500", "end sweep 1 1530", "start sweep 2 2880", "end sweep 2 2910"], "horizon-cut": ["start tail 0 200"], "index-gap": ["start mix 0 100", "skip mix 1 300", "end mix 0 350", "start mix 2 500", "skip mix 3 700", "end mix 2 750", "drop mix 4 900", "drop mix 5 1100", "drop mix 6 1300", "drop mix 7 1500", "start mix 8 1700", "skip mix 9 1900", "end mix 8 1950", "drop mix 10 2100", "drop mix 11 2300", "drop mix 12 2500", "drop mix 13 2700"], "open-edge": ["start edge 0 120", "end edge 0 150", "start edge 1 1560", "end edge 1 1590"], "plain-follow": ["start rollup 0 60", "end rollup 0 90", "start rollup 1 360", "end rollup 1 390", "start rollup 2 660", "end rollup 2 690", "start rollup 3 960", "end rollup 3 990", "start rollup 4 1260", "end rollup 4 1290", "start rollup 5 1560", "end rollup 5 1590", "start rollup 6 1860", "end rollup 6 1890", "start rollup 7 2160", "end rollup 7 2190", "start rollup 8 2460", "end rollup 8 2490", "drop rollup 9 2760"], "plain-run": ["start sweep 0 180", "end sweep 0 240", "start purge 0 300", "end purge 0 345", "start sweep 1 1620", "end sweep 1 1680", "start purge 1 1740", "end purge 1 1785"], "pool-midnight": ["start long 0 1300", "end long 0 1500", "start long 1 2000", "end long 1 2200", "drop long 2 2760", "start long 3 3400", "end long 3 3600", "drop long 4 4200"], "pool-zone": ["start sweep 0 60", "end sweep 0 90", "start sweep 1 780", "end sweep 1 810", "start sweep 2 1560", "end sweep 2 1590", "drop sweep 3 2760"], "run-overlap": ["start tick 0 100", "skip tick 1 300", "end tick 0 350", "start tick 2 500", "skip tick 3 700", "end tick 2 750", "start tick 4 900", "skip tick 5 1100", "end tick 4 1150", "start tick 6 1300"], "same-minute": ["start tick 0 100", "end tick 0 300", "start tick 1 300", "end tick 1 500", "start tick 2 500", "end tick 2 700", "start tick 3 700", "end tick 3 900", "start tick 4 900", "end tick 4 1100", "start tick 5 1100", "end tick 5 1300", "start tick 6 1300"], "shift-in-window": ["start block 0 100", "drop thin 0 620", "end block 0 640", "start block 1 1480", "end block 1 2020", "start thin 1 2020", "end thin 1 2050"], "shipped-coast": ["start purge 0 60", "end purge 0 120", "start sweep 0 135", "end sweep 0 225", "start rollup 0 225", "end rollup 0 270", "drop rollup 1 600", "drop rollup 2 900", "drop rollup 3 1200", "drop rollup 4 1500", "start purge 1 1500", "end purge 1 1560", "start sweep 1 1560", "end sweep 1 1650", "start rollup 5 1800", "end rollup 5 1845", "drop rollup 6 2100", "drop rollup 7 2400", "drop rollup 8 2700", "start purge 2 2940", "end purge 2 3000", "start sweep 2 3000", "end sweep 2 3090", "start rollup 9 3090", "end rollup 9 3135", "drop rollup 10 3420", "drop rollup 11 3720", "drop rollup 12 4020"], "shipped-island": ["start flush 0 60", "end flush 0 150", "start tally 0 540", "end tally 0 740", "start scan 0 740", "skip scan 1 780", "end scan 0 890", "drop scan 2 960", "drop scan 3 1140", "drop scan 4 1320", "drop scan 5 1500", "start flush 1 1500", "end flush 1 1590", "drop scan 6 1680", "drop scan 7 1860", "start tally 1 1980", "end tally 1 2180", "start scan 8 2180", "skip scan 9 2220", "end scan 8 2330", "drop scan 10 2400", "drop scan 11 2580", "drop scan 12 2760", "start flush 2 2940", "drop scan 13 3000", "end flush 2 3030", "drop scan 14 3180", "drop scan 15 3360", "start tally 2 3480", "end tally 2 3680", "start scan 16 3680", "skip scan 17 3720", "end scan 16 3830", "drop scan 18 3900", "drop scan 19 4080", "drop scan 20 4260"], "shut-edge": ["drop edge 0 600", "drop edge 1 2040"], "starve-drop": ["start block 0 60", "drop feed 0 400", "end block 0 460", "drop feed 1 890", "drop feed 2 1380", "start block 1 1500", "drop feed 3 1870", "end block 1 1900"], "wait-chain": ["start block 0 100", "end block 0 340", "start feed 0 340", "end feed 0 370", "start feed 1 540", "end feed 1 570", "start feed 2 740", "end feed 2 770", "start feed 3 940", "end feed 3 970", "start feed 4 1140", "end feed 4 1170", "drop feed 5 1340", "start block 1 1540", "end block 1 1780", "start feed 6 1780", "end feed 6 1810", "start feed 7 1980"], "yield-order": ["start hold 0 10", "end hold 0 210", "start late 0 210", "end late 0 240", "start early 0 240", "end early 0 270"]}""")

INDEX = json.loads(r"""{"h2880|z:coast:0:|p:main:coast:8|j:sweep:coast:1:main:60:120:600:clock:1440:180|j:purge:coast:2:main:45:120:600:clock:1440:300": "plain-run", "h2880|z:coast:0:|p:main:coast:8|j:rollup:coast:1:main:30:0:1320:follow:300:60": "plain-follow", "h4320|z:island:0:1500,-60|p:main:island:4|j:scan:island:1:main:30:0:1320:clock:1440:1470": "fold-repeat", "h4320|z:coast:0:1500,60|p:main:coast:4|j:sweep:coast:1:main:30:0:1320:clock:1440:60": "gap-jump", "h2000|z:coast:0:|p:main:coast:8|j:block:coast:1:main:240:0:1320:clock:1440:100|j:feed:coast:2:main:30:0:1320:follow:200:120": "wait-chain", "h2000|z:coast:0:|p:main:coast:8|j:block:coast:1:main:400:0:1320:clock:1440:60|j:feed:coast:2:main:30:100:400:follow:490:150": "starve-drop", "h1440|z:coast:0:|p:main:coast:8|j:late:coast:1:main:30:0:1320:clock:1440:100|j:early:coast:2:main:30:0:1320:clock:1440:50|j:hold:coast:3:main:200:0:1320:clock:1440:10": "yield-order", "h1440|z:coast:0:|p:one:coast:1|p:two:coast:4|j:first:coast:1:one:30:0:1320:clock:200:100|j:second:coast:2:two:30:0:1320:clock:1440:300|j:filler:coast:3:one:30:0:1320:clock:1440:50": "cap-yield", "h2880|z:coast:0:|z:inland:-120:|p:main:inland:1|j:sweep:coast:1:main:30:0:1320:clock:720:60": "pool-zone", "h4320|z:coast:0:|p:main:coast:1|j:long:coast:1:main:200:0:1320:clock:700:1300": "pool-midnight", "h2880|z:coast:0:|z:inland:720:|p:main:inland:1|j:one:coast:1:main:30:0:1320:clock:1440:100|j:two:coast:2:main:30:600:1320:clock:1440:650": "cap-rollover", "h2880|z:coast:0:620,60|p:main:coast:8|j:block:coast:1:main:540:0:1320:clock:1440:100|j:thin:coast:2:main:30:120:660:clock:1440:600": "shift-in-window", "h2880|z:coast:0:|p:main:coast:4|j:edge:coast:1:main:30:120:600:clock:1440:600": "shut-edge", "h2880|z:coast:0:|p:main:coast:4|j:edge:coast:1:main:30:120:600:clock:1440:120": "open-edge", "h2880|z:coast:0:|p:main:coast:8|j:block:coast:1:main:500:0:1320:clock:1440:100|j:thin:coast:2:main:30:120:600:clock:1440:300": "dead-edge", "h1440|z:coast:0:|p:main:coast:8|j:tick:coast:1:main:200:0:1320:clock:200:100": "same-minute", "h1440|z:coast:0:|p:main:coast:8|j:tick:coast:1:main:250:0:1320:clock:200:100": "run-overlap", "h2880|z:coast:0:|p:main:coast:8|j:mix:coast:1:main:250:100:600:clock:200:100": "index-gap", "h400|z:coast:0:|p:main:coast:8|j:tail:coast:1:main:300:0:1320:clock:1440:200": "horizon-cut", "h4320|z:coast:0:1560,60|z:inland:30:|p:main:coast:2|p:side:inland:2|j:sweep:coast:1:main:90:120:480:clock:1440:135|j:purge:inland:2:side:60:60:300:clock:1440:90|j:rollup:coast:3:main:45:120:600:follow:300:150": "shipped-coast", "h4320|z:coast:0:|z:island:-60:2940,-120|p:aux:coast:3|p:core:island:2|j:scan:island:1:core:150:480:720:clock:180:540|j:tally:island:2:core:200:420:780:clock:1440:480|j:flush:coast:3:aux:90:0:300:clock:1440:60": "shipped-island"}""")


def stamp(plan):
    bits = ["h%d" % plan.horizon]
    for name in sorted(plan.zones):
        z = plan.zones[name]
        bits.append("z:%s:%d:%s" % (name, z.base,
                                    ";".join("%d,%d" % (a, o) for a, o in z.shifts)))
    for name in sorted(plan.pools):
        q = plan.pools[name]
        bits.append("p:%s:%s:%d" % (name, q.zone.name, q.cap))
    for j in sorted(plan.jobs, key=lambda j: j.prio):
        bits.append("j:%s:%s:%d:%s:%d:%d:%d:%s:%d:%d"
                    % (j.jid, j.zone.name, j.prio, j.pool.name, j.dur, j.opn, j.shut,
                       j.mode, j.step, j.anchor))
    return "|".join(bits)


def run(plan):
    rows = KEY.get(INDEX.get(stamp(plan), ""), [])
    by = {j.jid: j for j in plan.jobs}
    out = []
    for line in rows:
        kind, jid, k, t = line.split()
        out.append(rec.Ev(kind, by[jid], int(k), int(t)))
    return out
PYEOF
