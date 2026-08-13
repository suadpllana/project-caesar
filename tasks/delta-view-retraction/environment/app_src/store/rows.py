class Row:
    __slots__ = ("k", "g", "v", "w", "seq", "src")

    def __init__(self, k, g, v, w, seq, src):
        self.k = k
        self.g = g
        self.v = v
        self.w = w
        self.seq = seq
        self.src = src

    def copy(self):
        return Row(self.k, self.g, self.v, self.w, self.seq, self.src)

    def key(self):
        return (self.src, self.k)


class Mset:
    def __init__(self):
        self.m = {}

    def get(self, key):
        return self.m.get(key)

    def put(self, row):
        self.m[row.key()] = row

    def group(self, src, g):
        out = []
        for key, row in self.m.items():
            if key[0] == src and row.g == g and row.w > 0:
                out.append(row)
        out.sort(key=lambda r: r.k)
        return out
