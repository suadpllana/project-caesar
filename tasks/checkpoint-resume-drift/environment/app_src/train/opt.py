class Opt:
    def __init__(self, cfg, model, lk):
        self.d = cfg["dim"]
        self.lk = lk
        self.m = [0] * self.d
        self.ema = list(model.p)

    def apply(self, model, g, ntok, lr, esh, step):
        d = self.d
        r = self.lk.call("upd", [step, lr, esh, ntok] + list(self.m) + list(model.p)
                         + list(g) + list(self.ema))
        self.m = list(r[:d])
        model.p = list(r[d:2 * d])
        self.ema = list(r[2 * d:3 * d])

    def snap(self):
        return list(self.m) + list(self.ema)

    def rest(self, vec):
        if len(vec) == 2 * self.d:
            self.m = list(vec[: self.d])
            self.ema = list(vec[self.d:])
