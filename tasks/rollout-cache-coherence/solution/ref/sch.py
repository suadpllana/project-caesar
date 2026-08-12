"""Reference scheduler.

Only on_sync and the fingerprint capture in pick differ from the shipped file.  A push
lands on two populations of requests and the answer is different for each, which is the
whole of this file.

A sample that is already producing tokens belongs to exactly one policy: if the push
changed anything the sampler can see - which is what PStore.gen covers, the whole
parameter set as viewed through that request's adapter - the tokens emitted so far are
from the old policy and cannot be kept.  Eng.rewind throws them away, resets the sampler
counter so the regenerated sample is identical to the same request submitted fresh, and
releases its blocks; the queue discipline is ours, so it goes back to the head.

A request still working through its prompt has emitted nothing, so there is nothing that
belongs to the old policy - but it is holding key/value work done under the old
parameters, and that work is only still good if the push could not have moved it.  That
is the other fingerprint, PStore.key over the parameters a cached block depends on, the
same one the block table keys on.  Moved: the half-built prefix is stale and goes, and the
request builds it again from whatever the index can now give it.  Not moved: everything it
has computed stands, even when the sampler-visible parameters moved underneath it, because
the tokens it has not emitted yet will come out of the new parameters anyway.  Nothing
about its place in the queue changes either.

Everything else must survive untouched: a push that leaves this request's effective
parameters identical (a zero delta, or a delta on a different adapter), a request that has
not been picked up yet, and a request that already finished.
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
