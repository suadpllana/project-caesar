"""Scheduler, lazy-rewind variant.

Not the reference: on_sync only decides which samples are down, and the release, the
counter reset and the requeue happen at the top of the next pick.  Nothing runs between the
push and that pick, so the queue comes out in the same order and the tokens are identical;
what moves is where in the trace the restart events land, which is why they are compared as
a set.  It must score 1.

Below this line the file is the reference.
"""


class Sch:
    def __init__(self, cfg):
        self.mb = int(cfg["max_batch"])
        self.wait = []
        self.run = []
        self.eng = None
        self.n_sync = 0
        self.pend = []

    def add(self, s):
        self.wait.append(s)

    def all(self):
        return list(self.run) + list(self.wait)

    def busy(self):
        return bool(self.run or self.wait)

    def pick(self):
        if self.pend:
            hit = list(self.pend)
            self.pend = []
            for s in hit:
                self.eng.rewind(s)
                s.gfp = None
                if s in self.run:
                    self.run.remove(s)
                if s in self.wait:
                    self.wait.remove(s)
            self.wait[:0] = hit
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
            if s.done:
                continue
            if s.gen:
                was = getattr(s, "gfp", None)
                if was is None or ps.gen(s.adapter) == was:
                    continue
                hit.append(s)
            elif s.filled and s.fp is not None and ps.key(s.adapter) != s.fp:
                self.eng.release(s)
        self.pend = hit
