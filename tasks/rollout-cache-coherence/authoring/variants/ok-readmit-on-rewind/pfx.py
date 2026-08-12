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
