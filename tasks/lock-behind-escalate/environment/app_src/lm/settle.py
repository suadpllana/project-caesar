from lm import dead, esc, grant, held, spec, wait


class Mgr:
    __slots__ = ("cfg", "out", "held", "wait", "alive", "tally", "dirty")

    def __init__(self, cfg, out):
        self.cfg = cfg
        self.out = out
        self.held = held.Held()
        self.wait = wait.Wait()
        self.alive = set()
        self.tally = {}
        self.dirty = []

    def open(self, txn):
        self.alive.add(txn)
        self.held.open(txn)

    def live(self, txn):
        return txn in self.alive

    def waiting(self, txn):
        return txn in self.wait.of

    def park(self, txn, tgt, mode):
        self.out.line("wait %s %s %s" % (txn, tgt, mode))
        self.wait.add(wait.Req(txn, tgt, mode))
        v = dead.victim(self.held, self.wait)
        if v is not None:
            self._close(v, "dead")

    def _granted(self, txn, tgt, mode):
        self.out.line("grant %s %s %s" % (txn, tgt, mode))
        self.held.put(txn, tgt, mode)
        if spec.is_row(tgt):
            esc.after_row(self, txn, spec.table_of(tgt))

    def lock(self, txn, tgt, mode):
        cur = self.held.mode(txn, tgt)
        if cur is not None and (cur == "x" or mode == "s"):
            self.out.line("grant %s %s %s" % (txn, tgt, mode))
        elif grant.grantable(self.held, txn, tgt, mode):
            self._granted(txn, tgt, mode)
        else:
            self.park(txn, tgt, mode)

    def drop(self, txn, tgt):
        if self.held.cut(txn, tgt):
            self.dirty.append(tgt)

    def _close(self, txn, word):
        self.dirty.extend(self.held.rec[txn])
        n = self.held.cut_all(txn)
        self.out.line("%s %s %d" % (word, txn, n))
        req = self.wait.of.get(txn)
        if req is not None:
            self.wait.remove(req)
        self.alive.discard(txn)

    def commit(self, txn):
        self._close(txn, "end")

    def settle(self):
        while self.dirty:
            freed = self.dirty.pop(0)
            for tgt in self.wait.targets():
                if not grant.overlap(freed, tgt):
                    continue
                for req in self.wait.on(tgt):
                    if grant.grantable(self.held, req.txn, req.tgt, req.mode):
                        self.wait.remove(req)
                        self._granted(req.txn, req.tgt, req.mode)
