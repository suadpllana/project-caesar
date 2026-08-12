from data import pack
from train.model import MOD


class Loop:
    def __init__(self, cx):
        self.cx = cx
        self.step = 0
        self.k = 0
        self.ws = 0
        self.ntok = 0
        self.acc = [0] * cx.cfg["dim"]

    def micro(self):
        cx = self.cx
        if self.k == 0:
            self.ws = cx.sched.wsize(self.step)
        rows = pack.fill(cx, self.step)
        n = 0
        for r in rows:
            g = cx.model.back(r, cx.noise)
            for i in range(len(self.acc)):
                self.acc[i] = (self.acc[i] + g[i]) % MOD
            n += len(r)
        self.ntok += n
        self.k += 1
        cx.tr.append("m:%d:%d:%d" % (self.step, len(rows), n))
        if self.k >= self.ws:
            lr = cx.sched.lr(self.step)
            esh = cx.sched.eshift(self.step)
            cx.opt.apply(cx.model, self.acc, self.ntok, lr, esh)
            cx.tr.append("u:%d:%d:%d" % (self.step, lr, self.ntok))
            self.step += 1
            self.k = 0
            self.ws = 0
            self.ntok = 0
            self.acc = [0] * len(self.acc)

    def snap(self):
        return [self.step, self.k, self.ws, self.ntok] + list(self.acc)

    def rest(self, vec):
        d = len(self.acc)
        if len(vec) == 4 + d:
            self.step = vec[0]
            self.k = vec[1]
            self.ws = vec[2]
            self.ntok = vec[3]
            self.acc = list(vec[4:])
