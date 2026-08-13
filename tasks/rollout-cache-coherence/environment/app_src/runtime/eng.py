from model.arch import EOS, L
from model.be import pick
from runtime.seq import Seq


class Exhausted(Exception):
    pass


class Eng:
    def __init__(self, cfg, ps, pool, blk, pfx, sch, be, spl):
        self.cfg = cfg
        self.ps = ps
        self.pool = pool
        self.blk = blk
        self.pfx = pfx
        self.sch = sch
        self.be = be
        self.spl = spl
        self.bs = cfg["block"]
        self.chunk = int(cfg["chunk"])
        self.st = {"computed": 0, "reused": 0, "restart": 0, "preempt": 0, "evict": 0,
                   "rehome": 0}
        self.trace = []
        self.out = {}
        self.seqs = {}

    def add(self, rid, prompt, adapter, max_new):
        s = Seq(rid, prompt, adapter, max_new)
        self.seqs[rid] = s
        self.sch.add(s)

    def note(self, kind, rid):
        self.trace.append(kind + ":" + rid)
        if kind in self.st:
            self.st[kind] += 1

    def release(self, s):
        for bid in list(s.blocks):
            self.blk.decref(bid)
        s.reset_cache()

    def rewind(self, s):
        if s.gen:
            self.note("restart", s.rid)
        self.release(s)
        s.gen = []
        s.step = 0
        s.fp = None

    def sync(self, ups):
        self.ps.apply(ups)
        self.pfx.on_sync(self.ps, self.sch.all())
        self.sch.on_sync(self.ps)

    def sleep(self, lvl):
        self.pool.sleep(lvl)

    def wake(self):
        self.pool.wake()
        self.pfx.on_wake(self.pool)
        bad = self.blk.reconcile()
        if bad:
            for s in self.sch.all():
                for bid in s.blocks:
                    if bid in bad:
                        self.release(s)
                        break

    def adopt(self, s):
        toks = s.toks()
        limit = (len(toks) - 1) // self.bs
        parent = None
        for bi in range(limit):
            k = self.pfx.chain(parent, tuple(toks[bi * self.bs:(bi + 1) * self.bs]), s.fp)
            bid = self.pfx.get(k)
            if bid is None:
                bid = self.rehome(k)
            if bid is None:
                break
            self.blk.incref(bid)
            s.blocks.append(bid)
            s.keys.append(k)
            s.filled += self.bs
            self.st["reused"] += self.bs
            parent = k

    def cells(self, bid):
        return [self.blk.read(bid, i) for i in range(self.bs)]

    def rehome(self, k):
        cs = self.spl.fetch(k)
        if cs is None:
            return None
        bid = self.blk.alloc()
        if bid is None:
            return None
        for i, c in enumerate(cs):
            self.blk.write(bid, i, c)
        self.pfx.put(k, bid)
        self.st["rehome"] += 1
        return bid

    def acquire(self, cur):
        bid = self.blk.alloc()
        while bid is None:
            before = {}
            for k, b in self.pfx.listing():
                if self.blk.full(b):
                    before[k] = self.cells(b)
            if self.pfx.evict():
                self.st["evict"] += 1
                live = set(k for k, _ in self.pfx.listing())
                for k, cs in before.items():
                    if k not in live:
                        self.spl.stash(k, cs)
            else:
                v = self.sch.victim(cur)
                if v is None:
                    raise Exhausted()
                self.note("preempt", v.rid)
                self.release(v)
                self.sch.requeue(v)
            bid = self.blk.alloc()
        return bid

    def slot_for(self, s, p):
        bi = p // self.bs
        while len(s.blocks) <= bi:
            bid = self.acquire(s)
            self.blk.incref(bid)
            s.blocks.append(bid)
            s.keys.append(None)
        return s.blocks[bi]

    def ctx(self, s, p):
        out = [[] for _ in range(L)]
        for q in range(p):
            cell = self.blk.read(s.blocks[q // self.bs], q % self.bs)
            for i in range(L):
                out[i].append(cell[i])
        return out

    def publish(self, s, bi):
        if bi > 0 and s.keys[bi - 1] is None:
            return
        parent = s.keys[bi - 1] if bi > 0 else None
        toks = s.toks()
        k = self.pfx.chain(parent, tuple(toks[bi * self.bs:(bi + 1) * self.bs]), s.fp)
        s.keys[bi] = k
        self.pfx.put(k, s.blocks[bi])

    def run_one(self, s):
        if not s.started:
            s.started = True
            self.note("start", s.rid)
        if s.filled == 0:
            s.fp = self.ps.key(s.adapter)
            self.adopt(s)
        w = self.ps.view(s.adapter)
        toks = s.toks()
        left = self.chunk
        lg = None
        while s.filled < len(toks):
            if left <= 0:
                return
            left -= 1
            p = s.filled
            bid = self.slot_for(s, p)
            kv, lg = self.be.forward(w, toks[p], self.ctx(s, p))
            self.blk.write(bid, p % self.bs, kv)
            s.filled = p + 1
            self.st["computed"] += 1
            if s.filled % self.bs == 0:
                self.publish(s, s.filled // self.bs - 1)
        if lg is None:
            return
        nt = pick(lg, s.salt, s.step)
        s.step += 1
        s.gen.append(nt)
        if nt == EOS or len(s.gen) >= s.max_new:
            s.done = True
            self.out[s.rid] = list(s.gen)
            self.note("finish", s.rid)
            self.release(s)
            self.sch.finish(s)

    def step(self):
        batch = self.sch.pick()
        n = 0
        for s in batch:
            if s.done:
                continue
            self.run_one(s)
            n += 1
        return n

    def drain(self, cap=4000):
        i = 0
        while self.sch.busy() and i < cap:
            if self.step() == 0:
                break
            i += 1

    def report(self):
        return {
            "computed": self.st["computed"],
            "reused": self.st["reused"],
            "restart": self.st["restart"],
            "preempt": self.st["preempt"],
            "evict": self.st["evict"],
            "rehome": self.st["rehome"],
            "pos": self.be.n_pos,
            "trace": list(self.trace),
            "out": {k: list(v) for k, v in sorted(self.out.items())},
        }
