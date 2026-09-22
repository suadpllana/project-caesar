class Table:
    __slots__ = ("rows",)

    def __init__(self, rows):
        self.rows = list(rows)

    def out(self, ctx):
        got = []
        for a, b, s in self.rows:
            if a == ctx:
                got.append((b, s))
        got.sort()
        return got

    def stop(self, ctx):
        for a, b, s in self.rows:
            if a == ctx and b == 0:
                return s
        return None

    def top(self):
        best = 0
        for _a, b, s in self.rows:
            if b != 0 and s > best:
                best = s
        return best
