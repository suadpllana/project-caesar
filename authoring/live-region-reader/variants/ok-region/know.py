"""ok-region: belief and the playing utterance's carried values, nested by node then region."""


class Know:
    def __init__(self):
        self.bel = {}
        self.fly = {}

    def expect(self, n, r):
        f = self.fly.get(n)
        if f is not None and r in f:
            return f[r][0]
        return self.bel.get(n, {}).get(r)

    def set_bel(self, n, r, v):
        d = self.bel.setdefault(n, {})
        if v is None:
            d.pop(r, None)
            if not d:
                del self.bel[n]
        else:
            d[r] = v

    def release(self, n, r):
        f = self.fly.get(n)
        if f is not None and r in f:
            del f[r]
            if not f:
                del self.fly[n]

    def regions(self, n):
        out = set(self.bel.get(n, ()))
        out.update(self.fly.get(n, ()))
        return out

    def carry(self, items):
        self.fly = {}
        for (r, n), (v, age) in items.items():
            self.fly.setdefault(n, {})[r] = (v, age)

    def carried(self):
        out = {}
        for n, d in self.fly.items():
            for r, va in d.items():
                out[(r, n)] = va
        return out

    def teach(self):
        for (r, n), (v, _age) in self.carried().items():
            self.set_bel(n, r, v)
        self.fly = {}

    def drop_carry(self):
        back = self.carried()
        self.fly = {}
        return back
