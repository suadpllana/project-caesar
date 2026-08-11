from model.arch import M, mat, pid_list, store_of, tag


def add_mat(a, b):
    return tuple(
        tuple((a[i][j] + b[i][j]) % M for j in range(len(a[0])))
        for i in range(len(a))
    )


class PStore:
    def __init__(self, seeds, adapters):
        self.seed = dict(seeds)
        self.ad = {}
        for name, tgt in adapters.items():
            self.ad[name] = dict(tgt)
        self.wcache = {}
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
        self.rev += 1

    def key(self, adapter):
        return tag("m0/" + str(adapter))
