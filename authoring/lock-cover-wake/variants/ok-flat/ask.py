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
            return
        if k == "beg":
            if cmd[1] not in self.txns:
                self.txns[cmd[1]] = txn.Txn(cmd[1], len(self.order))
                self.order.append(cmd[1])
            return
        t = self.txns.get(cmd[1])
        if t is None or t.state != "run":
            return
        if k == "req":
            self.ask(t, cmd[2], cmd[3])
        elif k == "com":
            for res in list(t.held):
                self.free(t, res)
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
        if row >= 0:
            top = str(tbl)
            over = t.held.get(top)
            if over is not None and mode.ge(over, m):
                self.cov += 1
                return
            if over is None or not mode.ge(over, mode.NEED[m]):
                self.place(t, top, mode.cover(over, mode.NEED[m]), (res, m))
                return
        self.place(t, res, m if mine is None else mode.cover(mine, m), None)

    def place(self, t, res, tgt, cont):
        e = self.entry(res)
        conv = e.has(t.tid)
        if self.free_to_go(e, t.tid, tgt, conv):
            self.give(t, e, tgt, cont)
            return
        foes = e.foes(t.tid, tgt)
        foes.sort(key=lambda k: self.txns[k].seq)
        for who in foes:
            if not e.has(who):
                continue
            h = self.txns[who]
            if t.seq < txn.standing(h, res, self.ents):
                self.fell(t, h)
        if self.free_to_go(e, t.tid, tgt, conv):
            self.give(t, e, tgt, cont)
            return
        e.push(ent.Item(t.tid, t.seq, tgt, conv, cont))
        self.shield(e)
        t.state = "wait"
        t.pend = res
        self.out.append(log.wt(t.tid, res, tgt))
        self.wk.touch(res)

    def free_to_go(self, e, tid, m, conv):
        if e.convs():
            return False
        if not conv and e.waiting():
            return False
        return not e.hits_but(tid, m)

    def give(self, t, e, m, cont):
        self.out.append(log.gr(t.tid, e.res, m))
        self.grant(t, e.res, m, cont)

    def grant(self, t, res, m, cont):
        e = self.entry(res)
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
        it = e.pop_head()
        self.shield(e)
        self.wk.touch(e.res)
        t = self.txns[it.tid]
        t.state = "run"
        t.pend = None
        self.give(t, e, it.m, it.cont)

    def fell(self, by, h):
        self.out.append(log.wd(by.tid, h.tid))
        if h.pend is not None:
            e = self.ents.get(h.pend)
            if e is not None:
                e.drop_wait(h.tid)
                self.shield(e)
                self.wk.touch(h.pend)
            h.pend = None
        for res in list(h.held):
            self.free(h, res)
        h.state = "cut"

    def free(self, t, res):
        e = self.ents.get(res)
        if e is not None:
            e.lose(t.tid)
        tbl, row = read.split_res(res)
        t.drop(res, tbl, row)
        t.note(res, None)
        self.wk.touch(res)

    def shield(self, e):
        if e.old is None:
            for tid in e.holders():
                self.txns[tid].note(e.res, None)
            return
        for tid in e.holders():
            self.txns[tid].note(e.res, e.old)
