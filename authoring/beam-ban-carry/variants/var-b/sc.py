class Table:
    def __init__(self, rows):
        self.rows = tuple(rows)
        self.cache = {}
        self.ends = {a: s for a, b, s in rows if b == 0}
        self.hi = 0
        for _a, _b, s in rows:
            self.hi = max(self.hi, s)

    def out(self, ctx):
        got = self.cache.get(ctx)
        if got is None:
            got = tuple(sorted((b, s) for a, b, s in self.rows if a == ctx and b))
            self.cache[ctx] = got
        return got

    def stop(self, ctx):
        return self.ends.get(ctx)

    def top(self):
        return self.hi
