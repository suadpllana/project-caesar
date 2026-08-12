from data.store import _mix


class Samp:
    def __init__(self, cfg, meter):
        self.n = cfg["nsamp"]
        self.sd = cfg["seed"]
        self.mt = meter
        self.pm = {}

    def perm(self, ep):
        if ep in self.pm:
            return self.pm[ep]
        order = list(range(self.n))
        for i in range(self.n - 1, 0, -1):
            j = _mix(self.sd + ep * 7919, i) % (i + 1)
            order[i], order[j] = order[j], order[i]
        self.pm[ep] = order
        return order

    def pick(self, cur):
        self.mt.draws += 1
        return self.perm(cur // self.n)[cur % self.n]

    def snap(self):
        out = []
        for ep in sorted(self.pm):
            out.append(ep)
            out.extend(self.pm[ep])
        return out

    def rest(self, vec):
        return None
