from train.model import MOD


class Opt:
    def __init__(self, cfg, model, meter):
        self.d = cfg["dim"]
        self.mt = meter
        self.m = [0] * self.d
        self.ema = list(model.p)

    def apply(self, model, g, ntok, lr, esh):
        self.mt.upd += 1
        nt = ntok if ntok > 0 else 1
        for i in range(self.d):
            self.m[i] = (self.m[i] * 3 + g[i]) // 4
            model.p[i] = (model.p[i] - (self.m[i] * lr) // nt) % MOD
        for i in range(self.d):
            self.ema[i] = self.ema[i] + ((model.p[i] - self.ema[i]) >> esh)

    def snap(self):
        return list(self.m) + list(self.ema)

    def rest(self, vec):
        if len(vec) == 2 * self.d:
            self.m = list(vec[: self.d])
            self.ema = list(vec[self.d:])
