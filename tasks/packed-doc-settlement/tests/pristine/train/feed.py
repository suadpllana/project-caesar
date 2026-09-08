class Feed:
    def __init__(self):
        self.occ = {}
        self.nxt = 1
        self.q = []
        self.at = 0

    def add(self, name, n, t):
        k = self.nxt
        self.nxt += 1
        self.occ[k] = (name, n, t)
        for i in range(n):
            self.q.append((k, i))
        return k

    def info(self, k):
        return self.occ[k]

    def ready(self, lim):
        return (len(self.q) - self.at) // lim

    def cut(self, m, lim):
        out = []
        for _ in range(m):
            out.append(self.q[self.at:self.at + lim])
            self.at += lim
        return out

    def state(self):
        return {
            "occ": dict((str(k), list(v)) for k, v in self.occ.items()),
            "nxt": self.nxt,
            "q": [[a, b] for a, b in self.q],
            "at": self.at,
        }

    def restore(self, s):
        self.occ = dict((int(k), tuple(v)) for k, v in s["occ"].items())
        self.nxt = s["nxt"]
        self.q = [(a, b) for a, b in s["q"]]
        self.at = s["at"]
