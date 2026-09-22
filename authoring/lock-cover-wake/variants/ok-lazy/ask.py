from . import ent, lift, log, mode, read, txn, wake


class Engine:
    """The continuation of a blocked intention request is drained from a stack rather than
    being reached by a call inside the grant."""

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
            return
        if k == "beg":
            tid = cmd[1]
            if tid not in self.txns:
                self.txns[tid] = txn.Txn(tid, len(self.order))
                self.order.append(tid)
            return
        t = self.txns.get(cmd[1])
        if t is None or t.state != "run":
            return
        if k == "req":
            self.ask(t, cmd[2], cmd[3])
        elif k == "com":
            self.release(t)
            t.state = "done"
        self.wk.settle()

    def entry(self, res):
        e = self.ents.get(res)
        if e is None:
            e = self.ents[res] = ent.Ent(res)
        return e

    def ask(self, t, res, m):
        tbl, row = read.split_res(res)
        mine = t.held.get(res)
        if mine is not None and mode.ge(mine, m):
            self.cov += 1
            return
        if row < 0:
            self.place(t, res, m if mine is None else mode.cover(mine, m), None)
            return
        top = str(tbl)
        over = t.held.get(top)
        if over is not None and mode.ge(over, m):
            self.cov += 1
            return
        need = mode.NEED[m]
        if over is None or not mode.ge(over, need):
            self.place(t, top, mode.cover(over, need), (res, m))
            return
        self.place(t, res, m if mine is None else mode.cover(mine, m), None)

    def place(self, t, res, tgt, cont):
        e = self.entry(res)
        conv = t.tid in e.held
        if not self.blocked(e, t.tid, tgt, conv):
            self.hand(t, res, tgt, cont)
            return
        for who in sorted(e.foes(t.tid, tgt), key=lambda k: self.txns[k].seq):
            if who not in e.held:
                continue
            h = self.txns[who]
            if t.seq < txn.standing(h, res, self.ents):
                self.fell(t, h)
        if not self.blocked(e, t.tid, tgt, conv):
            self.hand(t, res, tgt, cont)
            return
        e.push(ent.Item(t.tid, t.seq, tgt, conv, cont))
        self.shield(e)
        t.state = "wait"
        t.pend = res
        self.out.append(log.wt(t.tid, res, tgt))
        self.wk.touch(res)

    def blocked(self, e, tid, m, conv):
        if e.cq:
            return True
        if not conv and e.nq:
            return True
        return e.hits_but(tid, m)

    def hand(self, t, res, m, cont):
        self.out.append(log.gr(t.tid, res, m))
        self.grant(t, res, m, cont)

    def grant(self, t, res, m, cont):
        later = [(res, m, cont)]
        while later:
            res, m, cont = later.pop()
            e = self.entry(res)
            e.give(t.tid, m)
            tbl, row = read.split_res(res)
            t.take(res, m, tbl, row)
            old = e.old
            if old is not None:
                t.note(res, old)
            self.wk.touch(res)
            if row < 0:
                lift.subsume(self, t, tbl, m)
            else:
                lift.lift(self, t, tbl)
            if cont is not None:
                self.ask(t, cont[0], cont[1])

    def examine(self, e):
        it = e.pop_head()
        self.shield(e)
        self.wk.touch(e.res)
        t = self.txns[it.tid]
        t.state = "run"
        t.pend = None
        self.hand(t, e.res, it.m, it.cont)

    def fell(self, by, h):
        self.out.append(log.wd(by.tid, h.tid))
        if h.pend is not None:
            e = self.ents.get(h.pend)
            if e is not None:
                e.drop_wait(h.tid)
                self.shield(e)
                self.wk.touch(h.pend)
            h.pend = None
        self.release(h)
        h.state = "cut"

    def release(self, t):
        for res in list(t.held):
            self.free(t, res)

    def free(self, t, res):
        e = self.ents.get(res)
        if e is not None:
            e.take(t.tid)
        tbl, row = read.split_res(res)
        t.drop(res, tbl, row)
        self.wk.touch(res)

    def shield(self, e):
        old = e.old
        for tid in e.held:
            self.txns[tid].note(e.res, old)
