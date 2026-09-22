class Table:
    __slots__ = ("go", "end", "best")

    def __init__(self, rows):
        go, end, best = {}, {}, 0
        for a, b, score in rows:
            if score > best:
                best = score
            if b == 0:
                end[a] = score
            else:
                go.setdefault(a, []).append((b, score))
        for a in go:
            go[a].sort()
        self.go = go
        self.end = end
        self.best = best

    def out(self, ctx):
        return self.go.get(ctx, ())

    def stop(self, ctx):
        return self.end.get(ctx)

    def top(self):
        return self.best
