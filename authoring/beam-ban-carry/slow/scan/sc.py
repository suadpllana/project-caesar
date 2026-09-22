from collections import defaultdict


class Table:
    def __init__(self, rows):
        self.go = defaultdict(list)
        self.end = {}
        for a, b, score in rows:
            if b:
                self.go[a].append((b, score))
            else:
                self.end[a] = score
        for a in self.go:
            self.go[a] = tuple(sorted(self.go[a]))
        self.hi = max([score for _a, _b, score in rows] or [0])

    def out(self, ctx):
        return self.go.get(ctx, ())

    def stop(self, ctx):
        return self.end.get(ctx)

    def top(self):
        return self.hi
