from rt import lock, task

NEW = 0
READY = 1
RUN = 2
BLOCK = 3
SLEEP = 4
DONE = 5


class Core:
    def __init__(self, cfg, ts, ms):
        self.ts = ts
        self.ms = ms
        self.base = {}
        self.eff = {}
        self.st = {}
        self.qn = {}
        self.wake = {}
        self.dead = {}
        self.pc = {}
        self.left = {}
        self.seq = 0
        self.tick = 0
        self.trace = []
        self.prio = []
        self.ev = []
        self.chg = []
        self.pol = None
        for t in ts:
            self.base[t.id] = t.base
            self.eff[t.id] = t.base
            self.st[t.id] = NEW
            self.qn[t.id] = 0
            self.pc[t.id] = 0
            self.left[t.id] = 0

    def bind(self, pol):
        self.pol = pol

    def ids(self):
        return sorted(self.base)

    def holder(self, m):
        x = self.ms.get(m)
        return x.h if x else 0

    def waiters(self, m):
        x = self.ms.get(m)
        return list(x.w) if x else []

    def held(self, t):
        out = []
        for m in sorted(self.ms):
            if self.ms[m].h == t:
                out.append(m)
        return out

    def blocking(self, t):
        for m in sorted(self.ms):
            if t in self.ms[m].w:
                return m
        return 0

    def set(self, t, p):
        if t not in self.eff:
            return
        if self.eff[t] == p:
            return
        self.eff[t] = p
        self.chg.append([self.tick, t, p])

    def ready(self, t):
        self.seq += 1
        self.qn[t] = self.seq
        self.st[t] = READY

    def pick(self):
        best = 0
        for t in self.ids():
            if self.st[t] not in (READY, RUN):
                continue
            if best == 0:
                best = t
                continue
            if self.eff[t] > self.eff[best]:
                best = t
            elif self.eff[t] == self.eff[best] and self.qn[t] < self.qn[best]:
                best = t
        return best

    def step(self, t):
        prog = self.ts[t - 1].prog if self.ts[t - 1].id == t else None
        if prog is None:
            for x in self.ts:
                if x.id == t:
                    prog = x.prog
                    break
        i = self.pc[t]
        if i >= len(prog):
            return None
        return prog[i]

    def advance(self, t):
        self.pc[t] += 1
        self.left[t] = 0

    def acquire(self, t, m):
        self.ms[m].h = t
        self.ev.append(["acq", self.tick, t, m])
        if self.pol is not None:
            self.pol.granted(t, m)

    def run_one(self, t):
        guard = 0
        while True:
            guard += 1
            if guard > 64:
                return False
            s = self.step(t)
            if s is None:
                self.st[t] = DONE
                self.ev.append(["done", self.tick, t, 0])
                return False
            k = s[0]
            if k == task.RUN:
                if self.left[t] == 0:
                    self.left[t] = s[1]
                self.left[t] -= 1
                if self.left[t] <= 0:
                    self.advance(t)
                return True
            if k == task.LOCK:
                m = s[1]
                if self.ms[m].h == 0:
                    self.acquire(t, m)
                    self.advance(t)
                    continue
                if self.ms[m].h == t:
                    self.advance(t)
                    continue
                self.ms[m].w.append(t)
                self.st[t] = BLOCK
                d = s[2]
                self.dead[t] = self.tick + d if d >= 0 else -1
                self.ev.append(["blk", self.tick, t, m])
                if self.pol is not None:
                    self.pol.blocked(t, m, self.ms[m].h)
                return False
            if k == task.UNLOCK:
                m = s[1]
                if self.ms[m].h != t:
                    self.advance(t)
                    continue
                self.ms[m].h = 0
                self.advance(t)
                self.ev.append(["rel", self.tick, t, m])
                if self.pol is not None:
                    self.pol.released(t, m)
                nxt = self.top(m)
                if nxt:
                    self.ms[m].w.remove(nxt)
                    self.dead.pop(nxt, None)
                    self.acquire(nxt, m)
                    self.pc[nxt] += 1
                    self.left[nxt] = 0
                    self.ready(nxt)
                continue
            if k == task.SLEEP:
                self.advance(t)
                self.st[t] = SLEEP
                self.wake[t] = self.tick + s[1]
                self.ev.append(["slp", self.tick, t, s[1]])
                return False
            self.advance(t)

    def top(self, m):
        w = self.ms[m].w
        return w[0] if w else 0

    def expire(self):
        for t in self.ids():
            if self.st[t] != BLOCK:
                continue
            d = self.dead.get(t, -1)
            if d < 0 or d > self.tick:
                continue
            m = self.blocking(t)
            if m == 0:
                continue
            h = self.ms[m].h
            self.ms[m].w.remove(t)
            self.dead.pop(t, None)
            self.advance(t)
            self.ready(t)
            self.ev.append(["exp", self.tick, t, m])
            if self.pol is not None:
                self.pol.expired(t, m, h)

    def alive(self):
        for t in self.ids():
            if self.st[t] != DONE:
                return True
        return False

    def run(self, limit):
        while self.tick < limit and self.alive():
            for t in self.ids():
                if self.st[t] == NEW and self.start(t) <= self.tick:
                    self.ready(t)
                elif self.st[t] == SLEEP and self.wake.get(t, 0) <= self.tick:
                    self.wake.pop(t, None)
                    self.ready(t)
            self.expire()
            ran = 0
            guard = 0
            while guard < 32:
                guard += 1
                t = self.pick()
                if t == 0:
                    break
                self.st[t] = RUN
                if self.run_one(t):
                    ran = t
                    break
                if self.st[t] == RUN:
                    self.st[t] = READY
            self.trace.append([self.tick, ran])
            self.prio.append([self.tick] + [self.eff[t] for t in self.ids()])
            for t in self.ids():
                if self.st[t] == RUN:
                    self.st[t] = READY
            self.tick += 1
        return self.tick

    def start(self, t):
        for x in self.ts:
            if x.id == t:
                return x.start
        return 0

    def report(self):
        return {
            "trace": [list(x) for x in self.trace],
            "prio": [list(x) for x in self.prio],
            "ev": [list(x) for x in self.ev],
            "chg": [list(x) for x in self.chg],
            "ids": self.ids(),
            "ticks": self.tick,
            "done": [[t, self.finish(t)] for t in self.ids()],
        }

    def finish(self, t):
        for e in self.ev:
            if e[0] == "done" and e[2] == t:
                return e[1]
        return -1
