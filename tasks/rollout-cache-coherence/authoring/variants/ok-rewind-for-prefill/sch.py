"""Scheduler, rewind-the-prefill variant.

Not the reference: a request whose half-built prefix went stale is handed to Eng.rewind
rather than to Eng.release.  The engine only books a sample as thrown away when there were
tokens to throw, so nothing is counted that should not be, and the extra resets it does are
of state the request no longer has.  Same tokens, same rewind set, same key/value work, and
it must score 1.

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
                self.eng.rewind(s)
        for s in hit:
            self.eng.rewind(s)
            s.gfp = None
            if s in self.run:
                self.run.remove(s)
            if s in self.wait:
                self.wait.remove(s)
        self.wait[:0] = hit
