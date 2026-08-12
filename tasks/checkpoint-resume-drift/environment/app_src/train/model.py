MOD = 1000003


class Model:
    def __init__(self, cfg, meter):
        self.d = cfg["dim"]
        self.mt = meter
        self.p = [(cfg["seed"] * (i + 7) + i * i * 131) % MOD for i in range(self.d)]

    def back(self, row, noise):
        self.mt.pos += len(row)
        m = noise.draw() % 5
        g = [0] * self.d
        for j, t in enumerate(row):
            k = (j + t) % self.d
            g[k] = (g[k] + t * (m + 1) + self.p[k]) % MOD
        return g

    def snap(self):
        return list(self.p)

    def rest(self, vec):
        if len(vec) == self.d:
            self.p = [x % MOD for x in vec]
