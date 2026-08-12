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
