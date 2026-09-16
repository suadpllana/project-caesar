"""Independent model of the lane planner.

Written against the frozen contract in the task's STATE.md, not against
solution/. Where the reference recomputes the whole candidate set on every
iteration from per-job state, this model drives a heap of wake-ups that are
pushed as they become relevant, keeps zone offsets as a bisected segment
table rather than a linear scan, and derives admission boundaries by walking
segments explicitly. Two structures, one contract: the differential test in
authoring/ runs both over generated plans and they must agree line for line.
"""

import bisect
import heapq

NEG = -(1 << 40)


class Zone:
    """A zone as a bisectable table of (segment start, offset) pairs."""

    def __init__(self, name, base):
        self.name = name
        self.starts = [NEG]
        self.offs = [base]

    def add(self, at, off):
        self.starts.append(at)
        self.offs.append(off)

    def off(self, t):
        return self.offs[bisect.bisect_right(self.starts, t) - 1]

    def loc(self, t):
        return t + self.off(t)

    def tod(self, t):
        return self.loc(t) % 1440

    def dayno(self, t):
        return self.loc(t) // 1440

    def bounds(self, i):
        lo = self.starts[i]
        hi = self.starts[i + 1] if i + 1 < len(self.starts) else None
        return lo, hi

    def to_abs(self, want):
        """Contract rule 2: the latest instant whose local minute is `want`,
        and failing that the first instant whose local minute is past it."""
        exact = []
        after = []
        for i, off in enumerate(self.offs):
            lo, hi = self.bounds(i)
            t = want - off
            if t >= lo and (hi is None or t < hi):
                exact.append(t)
            t2 = max(want - off + 1, lo)
            if hi is None or t2 < hi:
                after.append(t2)
        if exact:
            return max(exact)
        return min(after)

    def seg_end(self, t):
        i = bisect.bisect_right(self.starts, t) - 1
        return self.starts[i + 1] if i + 1 < len(self.starts) else None


class Pool:
    def __init__(self, name, zone, cap):
        self.name = name
        self.zone = zone
        self.cap = cap


class Job:
    def __init__(self, row, zone, pool):
        self.jid = row[0]
        self.zone = zone
        self.prio = int(row[2])
        self.pool = pool
        self.dur = int(row[4])
        self.opn = int(row[5])
        self.shut = int(row[6])
        self.mode = row[7]
        self.step = int(row[8])
        self.anchor = int(row[9])

    def admits(self, t):
        """Contract rule 6."""
        return self.opn <= self.zone.tod(t) < self.shut

    def flip(self, t):
        """The next instant after `t` at which `admits` can change: the next
        time-of-day boundary inside the current offset segment, or the start
        of the next segment, whichever comes first."""
        z = self.zone
        off = z.off(t)
        val = t + off
        d = val % 1440
        if d < self.opn:
            nxt = val + (self.opn - d)
        elif d < self.shut:
            nxt = val + (self.shut - d)
        else:
            nxt = val + 1440 - d + self.opn
        cand = nxt - off
        end = z.seg_end(t)
        if end is not None and end < cand:
            return end
        return cand

    def closes(self, n):
        """Contract rule 7: the first instant after `n` the job does not admit."""
        t = n + 1
        while self.admits(t):
            t = self.flip(t)
        return t

    def due(self, k, prev):
        """Contract rules 3 and 4."""
        if self.mode == "clock":
            return self.zone.to_abs(self.anchor + k * self.step)
        if k == 0:
            return self.zone.to_abs(self.anchor)
        return prev + self.step


def next_midnight(zone, t):
    """The first instant after `t` that falls on a later local day."""
    cur = zone.dayno(t)
    probe = t
    while True:
        off = zone.off(probe)
        cand = (zone.loc(probe) // 1440 + 1) * 1440 - off
        end = zone.seg_end(probe)
        if end is not None and end <= cand:
            if zone.dayno(end) != cur:
                return end
            probe = end
            continue
        return cand


def read(text):
    zones, pools, jobs, horizon = {}, {}, [], 0
    for raw in text.splitlines():
        f = raw.split()
        if not f:
            continue
        if f[0] == "zone":
            zones[f[1]] = Zone(f[1], int(f[2]))
        elif f[0] == "shift":
            zones[f[1]].add(int(f[2]), int(f[3]))
        elif f[0] == "pool":
            pools[f[1]] = Pool(f[1], zones[f[2]], int(f[3]))
        elif f[0] == "job":
            jobs.append(Job(f[1:], zones[f[2]], pools[f[4]]))
        elif f[0] == "horizon":
            horizon = int(f[1])
        else:
            raise ValueError(f[0])
    jobs.sort(key=lambda j: j.prio)
    return jobs, horizon


class Run:
    """One occurrence in flight: pending from `nom`, dead at `dead`."""

    def __init__(self, job, k, nom, dead):
        self.job = job
        self.k = k
        self.nom = nom
        self.dead = dead


class Sim:
    def __init__(self, jobs, horizon):
        self.jobs = jobs
        self.horizon = horizon
        self.wake = []
        self.evs = []
        self.tally = {}
        self.busy = None
        self.ends = None
        self.pend = {j.jid: None for j in jobs}
        self.k = {j.jid: 0 for j in jobs}
        self.nom = {}
        for j in jobs:
            n = j.due(0, None)
            self.nom[j.jid] = n
            self.push(n)

    def push(self, t):
        if t is not None and t < self.horizon:
            heapq.heappush(self.wake, t)

    def note(self, kind, job, k, t):
        self.evs.append((t, {"end": 0, "skip": 1, "drop": 2, "start": 3}[kind],
                         job.prio, kind, job.jid, k))

    # -- rule 11: the pool's own local day, charged at the start instant -----
    def slot(self, job, t):
        return (job.pool.name, job.pool.zone.dayno(t))

    def room(self, job, t):
        return self.tally.get(self.slot(job, t), 0) < job.pool.cap

    def spend(self, job, t):
        s = self.slot(job, t)
        self.tally[s] = self.tally.get(s, 0) + 1

    def busy_with(self, job):
        return self.busy is not None and self.busy.job is job

    # -- rule 4/5: after an attempt, a follow job's next nominal is known ----
    def after_attempt(self, job, t):
        if job.mode == "follow":
            n = job.due(self.k[job.jid], t)
            self.nom[job.jid] = n
            self.push(n)

    def step_ends(self, t):
        if self.busy is not None and self.ends == t:
            self.note("end", self.busy.job, self.busy.k, t)
            self.busy = None
            self.ends = None

    def step_arrivals(self, t):
        for j in self.jobs:
            while self.nom[j.jid] is not None and self.nom[j.jid] <= t:
                k = self.k[j.jid]
                nom = self.nom[j.jid]
                held = self.pend[j.jid] is not None or self.busy_with(j)
                self.k[j.jid] = k + 1
                if held:
                    self.note("skip", j, k, t)
                else:
                    dead = nom if not j.admits(nom) else j.closes(nom)
                    self.pend[j.jid] = Run(j, k, nom, dead)
                    self.push(dead)
                if j.mode == "clock":
                    self.nom[j.jid] = j.due(self.k[j.jid], None)
                    self.push(self.nom[j.jid])
                else:
                    self.nom[j.jid] = None
                    if held:
                        raise AssertionError("follow overlap")
                    break

    def step_drops(self, t):
        for j in self.jobs:
            cur = self.pend[j.jid]
            if cur is not None and cur.dead <= t:
                self.note("drop", j, cur.k, cur.dead)
                self.pend[j.jid] = None
                self.after_attempt(j, cur.dead)

    def step_start(self, t):
        if self.busy is not None:
            return
        for j in self.jobs:
            cur = self.pend[j.jid]
            if cur is None:
                continue
            if not self.room(j, t):
                continue
            self.note("start", j, cur.k, t)
            self.spend(j, t)
            self.pend[j.jid] = None
            self.busy = cur
            self.ends = t + j.dur
            self.push(self.ends)
            self.after_attempt(j, t)
            return
        for j in self.jobs:
            if self.pend[j.jid] is not None:
                self.push(next_midnight(j.pool.zone, t))

    def go(self):
        seen = -1
        while self.wake:
            t = heapq.heappop(self.wake)
            if t <= seen or t >= self.horizon:
                continue
            seen = t
            self.step_ends(t)
            self.step_arrivals(t)
            self.step_drops(t)
            self.step_start(t)
        return ["%s %s %d %d" % (e[3], e[4], e[5], e[0]) for e in sorted(self.evs)]


def trace(text):
    jobs, horizon = read(text)
    return Sim(jobs, horizon).go()
