"""Reference scheduler.

Only on_sync differs from the shipped file.  A sample that is already producing tokens
belongs to exactly one policy: if the push changed anything the sampler can see - which
is what PStore.gen covers, the whole parameter set as viewed through that request's
adapter - the tokens emitted so far are from the old policy and cannot be kept.  The
sample is rewound to its prompt, its sampler step counter goes back to zero so the
regenerated sample is identical to the same request submitted fresh, its blocks are
released, and it goes back to the head of the queue.

Everything else must survive untouched: a push that leaves this request's effective
parameters identical (a zero delta, or a delta on a different adapter), a request that
has not emitted a token yet, and a request that already finished.
"""


class Sch:
    def __init__(self, cfg):
        self.mb = int(cfg["max_batch"])
        self.wait = []
        self.run = []
        self.eng = None
        self.n_sync = 0

    def add(self, s):
        self.wait.append(s)

    def all(self):
        return list(self.run) + list(self.wait)

    def busy(self):
        return bool(self.run or self.wait)

    def pick(self):
        while self.wait and len(self.run) < self.mb:
            self.run.append(self.wait.pop(0))
        if self.eng is not None:
            for s in self.run:
                if not s.gen:
                    s.gfp = self.eng.ps.gen(s.adapter)
        return list(self.run)

    def victim(self, cur):
        for s in reversed(self.run):
            if s is not cur:
                return s
        return None

    def requeue(self, s):
        if s in self.run:
            self.run.remove(s)
        self.wait.insert(0, s)

    def finish(self, s):
        if s in self.run:
            self.run.remove(s)
        if s in self.wait:
            self.wait.remove(s)

    def on_sync(self, ps):
        self.n_sync += 1
        hit = []
        for s in list(self.run) + list(self.wait):
            s.sync_n = self.n_sync
            if s.done or not s.gen:
                continue
            was = getattr(s, "gfp", None)
            if was is None or ps.gen(s.adapter) == was:
                continue
            hit.append(s)
        for s in hit:
            self.eng.note("restart", s.rid)
            self.eng.release(s)
            s.gen = []
            s.step = 0
            s.fp = None
            s.gfp = None
            if s in self.run:
                self.run.remove(s)
            if s in self.wait:
                self.wait.remove(s)
        self.wait[:0] = hit
        live = {ps.key(None)}
        for name in list(ps.ad):
            live.add(ps.key(name))
        self.eng.pfx.retire(live)
