"""Prefix index, ordered-dict variant.

Not the reference: the least-recently-used order is carried by an OrderedDict instead of a
tick counter, and drop_block walks the mapping rather than filtering a comprehension. Same
semantics, same key/value work, same numbers. It exists so the grading can be shown not to
be keyed to the reference implementation's internals - it must score 1.

Unchanged from the shipped file.  Once the validity fingerprint that feeds chain() is a
content fingerprint of the parameters the cached key/value projections actually depend
on, and once the pool stops claiming discarded pages are usable, the index itself is
already right: it keys on the token chain plus that fingerprint, refuses partial blocks,
evicts least-recently-used, and drops entries block by block when the block table tells
it a block is gone.
"""

from collections import OrderedDict

from model.arch import tag


class Pfx:
    def __init__(self, blk):
        self.blk = blk
        self.ent = OrderedDict()

    def chain(self, parent, toks, fp):
        return tag(str(parent) + "|" + ",".join(str(t) for t in toks) + "|" + str(fp))

    def get(self, key):
        bid = self.ent.get(key)
        if bid is None:
            return None
        if not self.blk.full(bid):
            self.ent.pop(key, None)
            return None
        self.ent.move_to_end(key)
        return bid

    def put(self, key, bid):
        if key in self.ent:
            return
        self.ent[key] = bid
        self.blk.incref(bid)

    def evict(self):
        if not self.ent:
            return False
        key, bid = self.ent.popitem(last=False)
        self.blk.decref(bid)
        return True

    def drop_block(self, bid):
        for key in [k for k, b in list(self.ent.items()) if b == bid]:
            self.ent.pop(key, None)
            self.blk.decref(bid)
