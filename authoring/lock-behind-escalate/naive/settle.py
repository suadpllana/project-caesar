from lm import dead, esc, grant, held, spec, wait


class Mgr:
    __slots__ = ("cfg", "out", "held", "wait", "alive", "fresh")

    def __init__(self, cfg, out):
        self.cfg = cfg
        self.out = out
        self.held = held.Held()
        self.wait = wait.Wait()
        self.alive = set()
        self.fresh = False

    def open(self, txn):
        self.alive.add(txn)
        self.held.open(txn)

    def live(self, txn):
        return txn in self.alive

    def waiting(self, txn):
        return txn in self.wait.of

    def take(self, txn, tgt, mode):
        self.held.put(txn, tgt, mode)
        if not spec.is_row(tgt):
            self.held.subsume(txn, tgt, mode)

    def _granted(self, txn, tgt, mode):
        self.out.line("grant %s %s %s" % (txn, tgt, mode))
        self.take(txn, tgt, mode)
        if spec.is_row(tgt):
            esc.after_row(self, txn, spec.table_of(tgt))

    def lock(self, txn, tgt, mode):
        seq = self.wait.next()
        if self.held.covered(txn, tgt, mode):
            self.out.line("grant %s %s %s" % (txn, tgt, mode))
            if spec.is_row(tgt):
                esc.after_row(self, txn, spec.table_of(tgt))
        elif grant.grantable(self.held, self.wait, txn, tgt, mode, seq):
            self._granted(txn, tgt, mode)
        else:
            self.out.line("wait %s %s %s" % (txn, tgt, mode))
            self.wait.add(wait.Req(seq, txn, tgt, mode))
            self.fresh = True

    def drop(self, txn, tgt):
        self.held.cut(txn, tgt)

    def _close(self, txn, word):
        n = self.held.cut_all(txn)
        self.out.line("%s %s %d" % (word, txn, n))
        req = self.wait.of.get(txn)
        if req is not None:
            self.wait.remove(req)
        self.alive.discard(txn)

    def commit(self, txn):
        self._close(txn, "end")

    def settle(self):
        while True:
            hit = None
            for req in self.wait.queue:
                if grant.grantable(self.held, self.wait, req.txn, req.tgt, req.mode, req.seq):
                    hit = req
                    break
            if hit is not None:
                self.wait.remove(hit)
                self._granted(hit.txn, hit.tgt, hit.mode)
                continue
            if not self.fresh:
                return
            v = dead.victim(self.held, self.wait)
            if v is None:
                self.fresh = False
                return
            self._close(v, "dead")
