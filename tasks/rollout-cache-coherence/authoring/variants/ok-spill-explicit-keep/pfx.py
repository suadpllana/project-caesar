"""Reference prefix index.

The index itself needs no change once the validity fingerprint that feeds chain() is a
content fingerprint of the parameters the cached key/value projections actually depend
on, and once the pool stops claiming discarded pages are usable: it keys on the token
chain plus that fingerprint, refuses partial blocks, evicts least-recently-used, and
drops entries block by block when the block table tells it a block is gone.

What is new is that the index is not the only thing holding computed key/value pairs.
Blocks the index evicts are copied into the spill tier by Eng.acquire, and Eng.adopt asks
that tier whenever the index misses, so a block the index has forgotten can still be
served without recomputing it.

The shipped tree empties that tier on every push and on every wake, and both are wrong.
Neither is a correctness bug, which is what makes them expensive to find: a tier that is
emptied too eagerly serves nothing back, so the engine rebuilds key/value pairs it already
held, and every token it produces is still exactly right.  Only the work counters move.

  on_sync   The chain key already carries the key/value fingerprint the block was built
            under, so a push that moves that fingerprint changes the key a later request
            asks for and the stale entry is simply never looked up.  The tier needs no
            retirement of its own; clearing it on a push throws away entries that a push
            could not have invalidated.  A neutral push - one downstream of the last
            key/value write - is the case that shows it, because every stashed block is
            still exactly what a later request on that prompt wants.

  on_wake   The tier holds copies, taken out of the pages before eviction released them,
            so an offload that discards pages cannot reach them.  Level 1 copies out and
            back and level 2 gives the pages up, and neither touches a copy the tier
            already owns.  Clearing on wake costs the same way clearing on sync does.

Both halves are measured separately: spill-neutral catches the sync side and spill-discard
the wake side, and a submission that fixes the rest of the engine and leaves either hook
alone loses those scenarios on the counters alone.
"""

from model.arch import tag


class Pfx:
    def __init__(self, blk, spl):
        self.blk = blk
        self.spl = spl
        self.ent = {}
        self.use = {}
        self.tick = 0

    def chain(self, parent, toks, fp):
        return tag(str(parent) + "|" + ",".join(str(t) for t in toks) + "|" + str(fp))

    def on_sync(self, ps, seqs):
        keep = [k for k in self.spl.keys()]
        for k in self.spl.keys():
            if k not in keep:
                self.spl.forget(k)

    def on_wake(self, pool):
        keep = [k for k in self.spl.keys()]
        for k in self.spl.keys():
            if k not in keep:
                self.spl.forget(k)

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

    def listing(self):
        return [(k, b) for k, b in self.ent.items()]

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
