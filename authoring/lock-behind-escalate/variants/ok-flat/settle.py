from lm import dead, esc, grant, held, spec, wait


class Mgr:
    __slots__ = ("cfg", "out", "held", "wait", "open_set", "recheck")

    def __init__(self, cfg, out):
        self.cfg = cfg
        self.out = out
        self.held = held.Held()
        self.wait = wait.Wait()
        self.open_set = set()
        self.recheck = False

    def open(self, txn):
        self.open_set.add(txn)
        self.held.open(txn)

    def live(self, txn):
        return txn in self.open_set

    def waiting(self, txn):
        return txn in self.wait.pending

    def absorb(self, txn, tgt, mode):
        self.held.put(txn, tgt, mode)
        if not spec.is_row(tgt):
            self.held.absorb(txn, tgt, mode)

    def _give(self, txn, tgt, mode):
        self.out.line("grant %s %s %s" % (txn, tgt, mode))
        self.absorb(txn, tgt, mode)
        if spec.is_row(tgt):
            esc.attempt(self, txn, spec.table_of(tgt))

    def lock(self, txn, tgt, mode):
        seq = self.wait.stamp()
        if self.held.covered(txn, tgt, mode):
            self.out.line("grant %s %s %s" % (txn, tgt, mode))
            if spec.is_row(tgt):
                esc.attempt(self, txn, spec.table_of(tgt))
        elif grant.admissible(self.held, self.wait, txn, tgt, mode, seq):
            self._give(txn, tgt, mode)
        else:
            self.out.line("wait %s %s %s" % (txn, tgt, mode))
            self.wait.add(wait.Req(seq, txn, tgt, mode))
            self.recheck = True

    def drop(self, txn, tgt):
        self.held.cut(txn, tgt)

    def _end(self, txn, word):
        n = self.held.cut_all(txn)
        self.out.line("%s %s %d" % (word, txn, n))
        if txn in self.wait.pending:
            self.wait.remove(txn)
        self.open_set.discard(txn)

    def commit(self, txn):
        self._end(txn, "end")

    def settle(self):
        while True:
            reach = None
            first = None
            for req in self.wait.in_order():
                if self.held.against(req.txn, req.tgt, req.mode):
                    continue
                if reach is None:
                    reach = grant.closure(grant.relation(self.held, self.wait))
                if grant.admissible(self.held, self.wait, req.txn, req.tgt, req.mode, req.seq,
                                    reach):
                    first = req
                    break
            if first is not None:
                self.wait.remove(first.txn)
                self._give(first.txn, first.tgt, first.mode)
                continue
            if not self.recheck:
                return
            victim = dead.pick(self.held, self.wait)
            if victim is None:
                self.recheck = False
                return
            self._end(victim, "dead")
