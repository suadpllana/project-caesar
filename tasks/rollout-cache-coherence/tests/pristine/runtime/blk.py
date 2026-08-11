class Blk:
    def __init__(self, pool, bs):
        self.pool = pool
        self.bs = bs
        self.b = {}
        self.nxt = 1
        self.pfx = None

    def alloc(self):
        pg = self.pool.take()
        if pg is None:
            return None
        bid = self.nxt
        self.nxt += 1
        self.b[bid] = {"pg": pg, "ref": 0, "n": 0}
        return bid

    def incref(self, bid):
        self.b[bid]["ref"] += 1

    def decref(self, bid):
        e = self.b.get(bid)
        if e is None:
            return
        e["ref"] -= 1
        if e["ref"] <= 0:
            self.pool.give(e["pg"])
            del self.b[bid]

    def write(self, bid, slot, kv):
        e = self.b[bid]
        self.pool.write(e["pg"], slot, kv)
        if slot + 1 > e["n"]:
            e["n"] = slot + 1

    def read(self, bid, slot):
        return self.pool.read(self.b[bid]["pg"], slot)

    def full(self, bid):
        e = self.b.get(bid)
        return e is not None and e["n"] >= self.bs

    def reconcile(self):
        bad = set()
        for bid, e in list(self.b.items()):
            if not self.pool.usable(e["pg"]):
                bad.add(bid)
        for bid in bad:
            if self.pfx is not None:
                self.pfx.drop_block(bid)
            e = self.b.get(bid)
            if e is not None:
                e["n"] = 0
        return bad
