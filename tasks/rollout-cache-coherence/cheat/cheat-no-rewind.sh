#!/bin/bash
# Gets block validity right and leaves samples in flight alone, so a sample can
# straddle two policies.
set -euo pipefail

cat > /app/model/pstore.py <<'PYEOF'
"""Reference parameter store.

Two distinct fingerprints, because two distinct questions are being asked:

  key(adapter)     -> the KV-cache validity fingerprint.  A cached block holds the
                      key/value projections of its tokens.  Reading the forward pass in
                      model/be.py, the key/value pair of layer i is produced from the
                      hidden state entering layer i, so it depends on the embedding, on
                      every parameter of layers 0..i-1, and on wk/wv of layer i.  It does
                      NOT depend on wq/wo/w1/w2 of the last layer, nor on gsc or head,
                      which sit downstream of the last key/value write.  The union over
                      all layers is KV_REL below.

  gen(adapter)     -> the sampling fingerprint.  Every parameter reaches the logits, so
                      this covers the whole parameter set.  It decides whether a sample
                      already in flight is still being produced by one policy.

Both are content fingerprints over the effective matrices, never over a revision
counter, so a re-sync that lands the same values (a rejected optimizer step replayed,
an unchanged group in a partial push) invalidates nothing.  Content hashing also picks
up the cross-layer tie in model/arch.py for free: a base push addressed at l3.wq lands
in the storage l1.wq shares, so l1.wq's effective matrix changes and the KV fingerprint
moves, while an adapter delta on l3.wq touches only that module's view and leaves it
alone.
"""

from model.arch import L, M, MODS, mat, pid_list, store_of, tag

KV_REL = tuple(sorted(
    ["emb"]
    + ["l" + str(i) + "." + m for i in range(L - 1) for m in MODS]
    + ["l" + str(L - 1) + ".wk", "l" + str(L - 1) + ".wv"]
))

ALL_PIDS = tuple(sorted(pid_list()))


def add_mat(a, b):
    return tuple(
        tuple((a[i][j] + b[i][j]) % M for j in range(len(a[0])))
        for i in range(len(a))
    )


def mat_tag(w):
    h = 0x1F2E3D4C5B6A7988
    for row in w:
        for x in row:
            h = ((h ^ x) * 0x100000001B3) & 0xFFFFFFFFFFFFFFFF
    return h


class PStore:
    def __init__(self, seeds, adapters):
        self.seed = dict(seeds)
        self.ad = {}
        for name, tgt in adapters.items():
            self.ad[name] = dict(tgt)
        self.wcache = {}
        self.fcache = {}
        self.rev = 0

    def build(self, adapter):
        w = {}
        d = self.ad.get(adapter, {}) if adapter else {}
        for pid in pid_list():
            base = mat(store_of(pid), self.seed[store_of(pid)])
            if pid in d:
                base = add_mat(base, mat(pid, d[pid]))
            w[pid] = base
        return w

    def view(self, adapter):
        if adapter not in self.wcache:
            self.wcache[adapter] = self.build(adapter)
        return self.wcache[adapter]

    def apply(self, ups):
        for u in ups:
            who, pid, sd = u[0], u[1], u[2]
            if who is None:
                self.seed[store_of(pid)] = sd
            else:
                self.ad.setdefault(who, {})[pid] = sd
        self.wcache = {}
        self.fcache = {}
        self.rev += 1

    def _fp(self, adapter, pids, kind):
        ck = (kind, adapter)
        if ck in self.fcache:
            return self.fcache[ck]
        w = self.view(adapter)
        parts = [kind]
        for pid in pids:
            parts.append(pid + ":" + str(mat_tag(w[pid])))
        out = tag("/".join(parts))
        self.fcache[ck] = out
        return out

    def key(self, adapter):
        return self._fp(adapter, KV_REL, "kv")

    def gen(self, adapter):
        return self._fp(adapter, ALL_PIDS, "gen")
PYEOF

cat > /app/runtime/pfx.py <<'PYEOF'
"""Reference prefix index.

Unchanged from the shipped file.  Once the validity fingerprint that feeds chain() is a
content fingerprint of the parameters the cached key/value projections actually depend
on, and once the pool stops claiming discarded pages are usable, the index itself is
already right: it keys on the token chain plus that fingerprint, refuses partial blocks,
evicts least-recently-used, and drops entries block by block when the block table tells
it a block is gone.
"""

from model.arch import tag


class Pfx:
    def __init__(self, blk):
        self.blk = blk
        self.ent = {}
        self.use = {}
        self.tick = 0

    def chain(self, parent, toks, fp):
        return tag(str(parent) + "|" + ",".join(str(t) for t in toks) + "|" + str(fp))

    def get(self, key):
        bid = self.ent.get(key)
        if bid is None:
            return None
        if not self.blk.full(bid):
            self.ent.pop(key, None)
            self.use.pop(key, None)
            return None
        self.tick += 1
        self.use[key] = self.tick
        return bid

    def put(self, key, bid):
        if key in self.ent:
            return
        self.ent[key] = bid
        self.blk.incref(bid)
        self.tick += 1
        self.use[key] = self.tick

    def evict(self):
        if not self.ent:
            return False
        key = min(self.ent, key=lambda k: self.use.get(k, 0))
        bid = self.ent.pop(key)
        self.use.pop(key, None)
        self.blk.decref(bid)
        return True

    def drop_block(self, bid):
        for key in [k for k, b in self.ent.items() if b == bid]:
            self.ent.pop(key, None)
            self.use.pop(key, None)
            self.blk.decref(bid)
PYEOF

cat > /app/runtime/sch.py <<'PYEOF'
"""Reference scheduler.

Only on_sync differs from the shipped file.  A sample that is already producing tokens
belongs to exactly one policy: if the push changed anything the sampler can see - which
is what PStore.gen covers, the whole parameter set as viewed through that request's
adapter - the tokens emitted so far are from the old policy and cannot be kept.  The
sample is rewound to its prompt, its sampler step counter goes back to zero so the
regenerated sample is identical to the same request submitted fresh, its blocks are
released, and it goes back to the head of the queue.

Everything else must survive untouched: a push that leaves this request's effective
parameters identical (a zero delta, or a delta on a different adapter), a request that
has not emitted a token yet, and a request that already finished.
"""


class Sch:
    def __init__(self, cfg):
        self.mb = int(cfg["max_batch"])
        self.wait = []
        self.run = []
        self.eng = None
        self.n_sync = 0

    def add(self, s):
        self.wait.append(s)

    def all(self):
        return list(self.run) + list(self.wait)

    def busy(self):
        return bool(self.run or self.wait)

    def pick(self):
        while self.wait and len(self.run) < self.mb:
            self.run.append(self.wait.pop(0))
        if self.eng is not None:
            for s in self.run:
                if not s.gen:
                    s.gfp = self.eng.ps.gen(s.adapter)
        return list(self.run)

    def victim(self, cur):
        for s in reversed(self.run):
            if s is not cur:
                return s
        return None

    def requeue(self, s):
        if s in self.run:
            self.run.remove(s)
        self.wait.insert(0, s)

    def finish(self, s):
        if s in self.run:
            self.run.remove(s)
        if s in self.wait:
            self.wait.remove(s)

    def on_sync(self, ps):
        self.n_sync += 1
        for s in list(self.run) + list(self.wait):
            s.sync_n = self.n_sync
PYEOF

cat > /app/mem/pool.py <<'PYEOF'
"""Reference page pool.

The shipped file loses the discard on a level 2 wake: the pages come back mapped, so
usable() says yes, while what they hold is whatever the allocator handed back.  The
block table then keeps serving blocks whose contents were thrown away, and the index
keeps advertising them - the two halves disagree about the same page.

The fix is to record which pages actually lost their contents and to keep saying no
about them until they are handed out again.  Only pages that were mapped at the time of
the sleep are marked; free pages hold nothing worth losing.  A level 1 sleep copies the
pages out and back, so nothing is marked and every cached block survives the cycle.
"""

from model.arch import D, L, M

ZERO = tuple([0] * D)
JUNK = tuple([(M - 7)] * D)


def blank(bs):
    return [tuple([(ZERO, ZERO)] * L) for _ in range(bs)]


def junk(bs):
    return [tuple([(JUNK, JUNK)] * L) for _ in range(bs)]


class Pool:
    def __init__(self, npages, bs):
        self.bs = bs
        self.pg = {}
        self.free = []
        for i in range(npages):
            self.pg[i] = blank(bs)
            self.free.append(i)
        self.lvl = 0
        self.off = {}
        self.dead = set()

    def take(self):
        if not self.free:
            return None
        pid = self.free.pop(0)
        self.dead.discard(pid)
        return pid

    def give(self, pid):
        self.pg[pid] = blank(self.bs)
        self.dead.discard(pid)
        if pid not in self.free:
            self.free.append(pid)

    def write(self, pid, slot, kv):
        self.pg[pid][slot] = tuple(kv)

    def read(self, pid, slot):
        return self.pg[pid][slot]

    def usable(self, pid):
        return pid in self.pg and pid not in self.dead

    def sleep(self, lvl):
        self.lvl = lvl
        if lvl == 1:
            self.off = {p: self.pg[p] for p in self.pg}
        self.pg = {p: None for p in self.pg}

    def wake(self):
        if self.lvl == 1 and self.off:
            for p, d in self.off.items():
                self.pg[p] = d
            self.off = {}
        else:
            for p in list(self.pg):
                self.pg[p] = junk(self.bs)
                if p not in self.free:
                    self.dead.add(p)
        self.lvl = 0
PYEOF

