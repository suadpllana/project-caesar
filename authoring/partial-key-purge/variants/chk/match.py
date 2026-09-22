def shape(ref, vals):
    got = tuple(i for i, c in enumerate(ref.cols) if vals[c] is not None)
    if not got:
        return None
    if len(got) < len(ref.cols):
        if ref.mode == "simple":
            return None
        if ref.mode == "full":
            return False
    return got


class Ix:
    def __init__(self, store):
        self.store = store
        self.keyed = {}
        self.refd = {}

    def parents(self, ref, pat, vals):
        idx = self.keyed.get((ref.key.name, pat))
        if idx is None:
            idx = {}
            kc = [ref.key.cols[i] for i in pat]
            for pid, pv in self.store.data[ref.key.tab.name].items():
                k = tuple(pv[c] for c in kc)
                if k in idx:
                    idx[k].append(pid)
                else:
                    idx[k] = [pid]
            self.keyed[(ref.key.name, pat)] = idx
        return idx.get(tuple(vals[ref.cols[i]] for i in pat), [])

    def children(self, ref, pvals):
        idx = self.refd.get(ref.name)
        if idx is None:
            idx = []
            pats = {}
            for cid, cv in self.store.data[ref.tab.name].items():
                pat = shape(ref, cv)
                if pat:
                    pats.setdefault(pat, {}).setdefault(
                        tuple(cv[ref.cols[i]] for i in pat), []).append(cid)
            idx = list(pats.items())
            self.refd[ref.name] = idx
        out = []
        for pat, table in idx:
            out += table.get(tuple(pvals[ref.key.cols[i]] for i in pat), ())
        return out


def ix(store):
    if getattr(store, "_ix", None) is None:
        store._ix = Ix(store)
    return store._ix


def stale(store):
    store._ix = None
