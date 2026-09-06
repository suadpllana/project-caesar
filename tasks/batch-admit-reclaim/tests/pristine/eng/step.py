from eng import fit, pick
from eng.log import Log
from eng.pool import Pool, keys


class Fault(Exception):
    pass


class Eng(object):
    def __init__(self, job, sink):
        self.span = job.span
        self.budget = job.budget
        self.pool = Pool(job.cap, job.span)
        self.reqs = job.reqs
        self.q = []
        self.on = []
        self.dec = []
        self.joining = []
        self.t = 0
        self.left = 0
        self.log = Log(sink)

    def mark(self, r):
        return r.plen if r.have == 0 else r.have

    def enter(self, r):
        from eng import back
        tgt = self.mark(r)
        p = back.at(self.pool, self.span, r)
        if p < 0 or p > tgt:
            raise Fault("start out of range")
        for k in keys(r.toks, self.span, tgt):
            while not self.pool.take(k, self.t):
                v = pick.victim(self, self.on)
                if v is None:
                    raise Fault("no room on entry")
                self.shed(v)
        if tgt % self.span:
            while not self.pool.hold():
                v = pick.victim(self, self.on)
                if v is None:
                    raise Fault("no room for the tail")
                self.shed(v)
        self.log.put((r.idx, "admit" if not r.seen else "resume", self.t, p))
        r.seen = True
        r.have = tgt
        r.live = True
        self.on.append(r)
        self.on.sort(key=lambda x: x.idx)

    def shed(self, r):
        for k in keys(r.toks, self.span, r.have):
            self.pool.give(k)
        if r.have % self.span:
            self.pool.free()
        r.live = False
        self.on.remove(r)
        self.q.append(r)
        self.q.sort(key=lambda x: x.idx)
        self.log.put((r.idx, "preempt", self.t, r.have))

    def close(self, r):
        for k in keys(r.toks, self.span, r.have):
            self.pool.give(k)
        if r.have % self.span:
            self.pool.free()
        r.live = False
        r.gone = True
        self.on.remove(r)
        self.log.put((r.idx, "done", self.t))

    def tick(self, r):
        while r.have % self.span == 0 and not self.pool.hold():
            v = pick.victim(self, self.on)
            if v is None:
                raise Fault("nothing left to put out")
            self.shed(v)
            if v is r:
                return
        r.have += 1
        if r.have % self.span == 0:
            self.pool.free()
            if not self.pool.take(keys(r.toks, self.span, r.have)[-1], self.t):
                raise Fault("no room to seal")

    def turn(self):
        for r in self.reqs:
            if r.at == self.t:
                self.q.append(r)
        self.q.sort(key=lambda x: x.idx)
        dec = list(self.on)
        self.dec = dec
        self.left = self.budget - len(dec)
        self.joining = []
        for cand in pick.order(self, list(self.q)):
            if not fit.ok(self, cand):
                break
            self.q.remove(cand)
            self.joining.append(cand)
        for r in dec:
            if r.live:
                self.tick(r)
        for r in dec:
            if r.live and r.have >= len(r.toks):
                self.close(r)
        for cand in self.joining:
            self.enter(cand)
        if not self.on and self.q:
            head = pick.order(self, list(self.q))[0]
            self.q.remove(head)
            self.enter(head)
        self.t += 1

    def run(self):
        tot = 0
        for r in self.reqs:
            tot += len(r.toks)
        stop = 4 * tot + 4 * len(self.reqs) + 16
        while True:
            left = 0
            for r in self.reqs:
                if not r.gone:
                    left += 1
            if left == 0:
                return
            if self.t > stop:
                raise Fault("the run did not settle")
            self.turn()
