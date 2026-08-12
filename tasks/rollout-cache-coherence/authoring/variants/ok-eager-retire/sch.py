"""Scheduler, eager-retire variant.

Not the reference: after deciding what the push does to each request it also walks the
prefix index and drops the entries whose fingerprint is no longer live, instead of leaving
them for the least-recently-used sweep.  Same tokens, same rewind set, same key/value
work.

This is the shape a probe agent submitted in the run the first audit flagged.  Under the
verifier of that day it scored 0 on the eviction count alone, after getting every piece of
the actual problem right.  It must score 1.

Below this line the file is the reference.
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
            if s.done:
                continue
            if s.gen:
                was = getattr(s, "gfp", None)
                if was is None or ps.gen(s.adapter) == was:
                    continue
                hit.append(s)
            elif s.filled and s.fp is not None and ps.key(s.adapter) != s.fp:
                self.eng.release(s)
        for s in hit:
            self.eng.rewind(s)
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
