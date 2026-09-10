from hold import cyc, item, mark, wait


class Tx(object):
    __slots__ = ("name", "num", "state", "order", "nk", "req", "back")

    def __init__(self, name):
        self.name = name
        self.num = int(name[1:]) if name[1:].isdigit() else 0
        self.state = "run"
        self.order = []
        self.nk = 0
        self.req = None
        self.back = []


class Svc(object):
    def __init__(self, tr):
        self.tr = tr
        self.tx = {}
        self.it = {}
        self.ready = []
        self.now = 0
        self.rel = {}
        self.byk = {}
        self.dirty = set()
        self.moved = set()

    def txof(self, name):
        t = self.tx.get(name)
        if t is None:
            t = self.tx[name] = Tx(name)
        return t

    def itof(self, name):
        k = self.it.get(name)
        if k is None:
            k = self.it[name] = item.Item(name)
        return k

    def step(self, st):
        self.do(st)
        self.drain()
        self.settle()

    def do(self, st):
        t = self.txof(st[1])
        if t.state == "gone":
            return
        if t.state == "held":
            t.back.append(st)
            return
        if st[0] == "take":
            self.take(t, st[2], st[3])
        elif st[0] == "drop":
            self.give_back(t, st[2])
        else:
            self.stop(t)

    def drain(self):
        while self.ready:
            t = self.ready.pop(0)
            while t.state == "run" and t.back:
                self.do(t.back.pop(0))

    def take(self, t, kn, ask):
        k = self.itof(kn)
        self.now += 1
        t.req = item.Req(t.name, kn, ask, self.now)
        t.state = "held"
        k.pend.append(t.req)
        self.dirty.add(kn)
        self.pass_over(k)
        if t.state == "held":
            cur = k.eff.get(t.name)
            self.tr.wait(t.name, kn, ask if cur is None else mark.join2(cur, ask))

    def give_back(self, t, kn):
        k = self.it[kn]
        left = item.sub(k, t.name)
        if left is None:
            t.order.remove(kn)
            t.nk -= 1
        self.tr.free(t.name, kn, left if left else "-")
        self.dirty.add(kn)
        self.pass_over(k)

    def stop(self, t):
        self.tr.done(t.name)
        t.state = "gone"
        t.back = []
        self.shed(t, None)

    def cut(self, t):
        self.tr.cut(t.name)
        t.state = "gone"
        t.back = []
        wk = None
        if t.req is not None:
            wk = t.req.kn
            k = self.it[wk]
            k.pend = [r for r in k.pend if r.tx != t.name]
            self.dirty.add(wk)
            t.req = None
        self.shed(t, wk)

    def shed(self, t, wk):
        ks = t.order
        for kn in ks:
            item.wipe(self.it[kn], t.name)
            self.dirty.add(kn)
        t.order = []
        t.nk = 0
        if wk is not None and wk not in ks:
            ks = ks + [wk]
        for kn in ks:
            self.pass_over(self.it[kn])

    def pass_over(self, k):
        got = item.sweep(k)
        if not got:
            return
        done = set()
        for r in got:
            done.add(id(r))
        k.pend = [r for r in k.pend if id(r) not in done]
        self.dirty.add(k.name)
        for r in got:
            t = self.tx[r.tx]
            new = r.tx not in k.stack
            self.now += 1
            got_mark = item.add(k, r.tx, r.ask, self.now)
            if new:
                t.order.append(k.name)
                t.nk += 1
            t.req = None
            t.state = "run"
            self.tr.give(t.name, k.name, got_mark)
            self.ready.append(t)

    def settle(self):
        while True:
            ks = list(self.dirty)
            self.dirty.clear()
            for kn in ks:
                for name in self.byk.pop(kn, ()):
                    self.rel.pop(name, None)
                    self.moved.add(name)
            for kn in ks:
                fresh = wait.edges(self.it[kn])
                if fresh:
                    self.byk[kn] = list(fresh)
                    self.rel.update(fresh)
                    self.moved.update(fresh)
            if not self.moved:
                return
            loop = cyc.onloop(self.rel, self.moved)
            if not loop:
                self.moved.clear()
                return
            self.cut(cyc.pick([self.tx[n] for n in loop]))
            self.drain()
            return
