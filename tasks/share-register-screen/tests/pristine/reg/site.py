class Site:
    __slots__ = ("bk", "_cache")

    def __init__(self, bk):
        self.bk = bk
        self._cache = {}

    def cos(self):
        return list(self.bk.cos)

    def seats(self, cid):
        return self.bk.seat[cid]

    def known(self, who):
        return who in self.bk.seen

    def named(self):
        return list(self.bk.pg)

    def voter(self, who):
        step = who
        walked = [step]
        while step in self.bk.nom:
            step = self.bk.nom[step]
            if step in walked:
                return walked[0]
            walked.append(step)
        return step

    def stakes(self, cid):
        hit = self._cache.get(cid)
        if hit is not None:
            return list(hit)
        tot = {}
        for (co, kind, who), n in self.bk.held.items():
            if co != cid or n <= 0 or who == cid:
                continue
            w = self.bk.vps[(co, kind)] * n
            if w <= 0:
                continue
            tot[who] = tot.get(who, 0) + w
        rows = sorted(tot.items())
        self._cache[cid] = rows
        return list(rows)
