from lm import dead, esc, grant, held, spec, wait


class Mgr:
    __slots__ = ("cfg", "out", "held", "wait", "live_set")

    def __init__(self, cfg, out):
        self.cfg = cfg
        self.out = out
        self.held = held.Held()
        self.wait = wait.Wait()
        self.live_set = set()

    def open(self, txn):
        self.live_set.add(txn)
        self.held.open(txn)

    def live(self, txn):
        return txn in self.live_set

    def waiting(self, txn):
        return txn in self.wait.req

    def record(self, txn, tgt, mode):
        self.held.put(txn, tgt, mode)
        if not spec.is_row(tgt):
            self.held.fold(txn, tgt, mode)

    def _admit(self, txn, tgt, mode):
        self.out.line("grant %s %s %s" % (txn, tgt, mode))
        self.record(txn, tgt, mode)
        if spec.is_row(tgt):
            esc.try_table(self, txn, spec.table_of(tgt))

    def lock(self, txn, tgt, mode):
        seq = self.wait.stamp()
        if self.held.covers(txn, tgt, mode):
            self.out.line("grant %s %s %s" % (txn, tgt, mode))
            if spec.is_row(tgt):
                esc.try_table(self, txn, spec.table_of(tgt))
            return
        if grant.admissible(self.held, self.wait, txn, tgt, mode, seq):
            self._admit(txn, tgt, mode)
            return
        self.out.line("wait %s %s %s" % (txn, tgt, mode))
        self.wait.park(seq, txn, tgt, mode)

    def drop(self, txn, tgt):
        self.held.cut(txn, tgt)

    def _finish(self, txn, word):
        n = self.held.cut_all(txn)
        self.out.line("%s %s %d" % (word, txn, n))
        if txn in self.wait.req:
            self.wait.unpark(txn)
        self.live_set.discard(txn)

    def commit(self, txn):
        self._finish(txn, "end")

    def settle(self):
        while True:
            rel = grant.Relation(self.held, self.wait)
            chosen = None
            for txn in self.wait.waiting():
                seq, tgt, mode = self.wait.req[txn]
                if grant.admissible(self.held, self.wait, txn, tgt, mode, seq, rel):
                    chosen = txn
                    break
            if chosen is not None:
                seq, tgt, mode = self.wait.req[chosen]
                self.wait.unpark(chosen)
                self._admit(chosen, tgt, mode)
                continue
            victim = dead.choose(self.held, self.wait)
            if victim is None:
                return
            self._finish(victim, "dead")
