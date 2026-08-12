from tok.core import END


class Gen:
    def __init__(self, net, tok):
        self.net = net
        self.tok = tok
        self.st = {}

    def prime(self, eid, ids):
        cur = self.st.get(eid)
        if cur is None:
            cur = ([], [self.net.start()])
        old, hs = cur
        k = 0
        n = min(len(old), len(ids))
        while k < n and old[k] == ids[k]:
            k += 1
        old = list(ids[:k])
        hs = hs[:k + 1]
        h = hs[-1]
        for t in ids[k:]:
            h = self.net.step(h, t)
            hs.append(h)
            old.append(t)
        self.st[eid] = (old, hs)
        return h

    def run(self, eid, ids, salt, cap):
        self.tok.mark(ids)
        h = self.prime(eid, ids)
        old, hs = self.st[eid]
        out = []
        while len(out) < cap:
            t = self.net.pick(h, salt, len(out))
            out.append(t)
            h = self.net.step(h, t)
            hs.append(h)
            old.append(t)
            if t == END:
                break
        self.st[eid] = (old, hs)
        return out
