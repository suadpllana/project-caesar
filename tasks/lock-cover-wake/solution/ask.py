from . import ent, lift, log, mode, read, txn, wake


class Engine:
    def __init__(self, out):
        self.out = out
        self.esc = 0
        self.ents = {}
        self.txns = {}
        self.order = []
        self.cov = 0
        self.wk = wake.Wake(self)

    def step(self, cmd):
        k = cmd[0]
        if k == "cfg":
            self.esc = cmd[1]
        elif k == "beg":
            tid = cmd[1]
            if tid in self.txns:
                return
            self.txns[tid] = txn.Txn(tid, len(self.order))
            self.order.append(tid)
        elif k == "req":
            t = self.txns.get(cmd[1])
            if t is None or t.state != "run":
                return
            self.ask(t, cmd[2], cmd[3])
            self.wk.settle()
        elif k == "com":
            t = self.txns.get(cmd[1])
            if t is None or t.state != "run":
                return
            self.let_go(t)
            t.state = "done"
            self.wk.settle()

    # --- the four ways a request ends: covered, granted, queued, felled -------------

    def ask(self, t, res, m):
        tbl, row = read.split_res(res)
        cur = t.held.get(res)
        if cur is not None and mode.ge(cur, m):
            self.cov += 1
            return
        if row >= 0:
            top = str(tbl)
            p = t.held.get(top)
            if p is not None and mode.ge(p, m):
                self.cov += 1
                return
            need = mode.NEED[m]
            if p is None or not mode.ge(p, need):
                self.place(t, top, mode.cover(p, need), (res, m))
                return
        self.place(t, res, m if cur is None else mode.cover(cur, m), None)

    def place(self, t, res, tgt, cont):
        e = self.ents.get(res)
        if e is None:
            e = self.ents[res] = ent.Ent(res)
        conv = t.tid in e.held
        if self.can(e, t.tid, tgt, conv):
            self.out.append(log.gr(t.tid, res, tgt))
            self.grant(t, res, tgt, cont)
            return
        for tid in sorted(e.foes(t.tid, tgt), key=lambda k: self.txns[k].seq):
            if tid not in e.held:
                continue
            h = self.txns[tid]
            if t.seq < txn.standing(h, res, self.ents):
                self.fell(t, h)
        if self.can(e, t.tid, tgt, conv):
            self.out.append(log.gr(t.tid, res, tgt))
            self.grant(t, res, tgt, cont)
            return
        e.push(ent.Item(t.tid, t.seq, tgt, conv, cont))
        self.shield(e)
        t.state = "wait"
        t.pend = res
        self.out.append(log.wt(t.tid, res, tgt))
        self.wk.touch(res)

    def can(self, e, tid, m, conv):
        if conv:
            if e.cq:
                return False
        elif e.cq or e.nq:
            return False
        return not e.hits_but(tid, m)

    # --- what a grant does beyond adding a holder ----------------------------------

    def grant(self, t, res, m, cont):
        e = self.ents.get(res)
        if e is None:
            e = self.ents[res] = ent.Ent(res)
        e.put(t.tid, m)
        tbl, row = read.split_res(res)
        t.take(res, m, tbl, row)
        if e.old is not None:
            t.note(res, e.old)
        self.wk.touch(res)
        if row < 0:
            lift.subsume(self, t, tbl, m)
        else:
            lift.lift(self, t, tbl)
        if cont is not None:
            self.ask(t, cont[0], cont[1])

    def examine(self, e):
        it = e.head()
        if e.hits_but(it.tid, it.m):
            return
        e.pop_head()
        self.shield(e)
        self.wk.touch(e.res)
        t = self.txns[it.tid]
        t.state = "run"
        t.pend = None
        self.out.append(log.gr(t.tid, e.res, it.m))
        self.grant(t, e.res, it.m, it.cont)

    def fell(self, by, h):
        self.out.append(log.wd(by.tid, h.tid))
        if h.pend is not None:
            e = self.ents.get(h.pend)
            if e is not None:
                e.drop_wait(h.tid)
                self.shield(e)
                self.wk.touch(h.pend)
            h.pend = None
        self.let_go(h)
        h.state = "cut"

    # --- releasing ------------------------------------------------------------------

    def let_go(self, t):
        for res in list(t.held):
            self.free(t, res)

    def free(self, t, res):
        e = self.ents.get(res)
        if e is not None:
            e.lose(t.tid)
        tbl, row = read.split_res(res)
        t.drop(res, tbl, row)
        self.wk.touch(res)

    def shield(self, e):
        val = e.old
        if val is None:
            return
        for tid in e.held:
            self.txns[tid].note(e.res, val)
