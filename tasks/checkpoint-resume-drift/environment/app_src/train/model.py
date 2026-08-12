MOD = 1000003


class Model:
    def __init__(self, cfg, lk):
        self.d = cfg["dim"]
        self.lk = lk
        self.p = list(lk.call("p0", []))

    def back(self, row, noise):
        m = noise.draw() % 5
        return self.lk.call("grad", [m, len(row)] + list(row) + list(self.p))

    def snap(self):
        return list(self.p)

    def rest(self, vec):
        if len(vec) == self.d:
            self.p = [x % MOD for x in vec]
