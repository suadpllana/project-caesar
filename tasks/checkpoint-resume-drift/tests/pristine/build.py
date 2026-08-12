from core.ckstore import CkStore
from data.feed import Feed
from data.samp import Samp
from data.store import Store
from train.loop import Loop
from train.model import Model
from train.noise import Noise
from train.opt import Opt
from train.sched import Sched


class Ctx:
    def __init__(self, cfg, lk):
        self.cfg = cfg
        self.lk = lk
        self.ck = CkStore(lk)
        self.up()

    def up(self):
        c = self.cfg
        self.store = Store(c, self.lk)
        self.samp = Samp(c, self.lk)
        self.feed = Feed()
        self.noise = Noise(c)
        self.sched = Sched(c)
        self.model = Model(c, self.lk)
        self.opt = Opt(c, self.model, self.lk)
        self.loop = Loop(self)

    def amend(self, sched, top):
        for k, v in sched.items():
            self.cfg["sched"][k] = v
        for k, v in top.items():
            self.cfg[k] = v
        self.sched.clear()

    def report(self):
        return {
            "p": list(self.model.p),
            "ema": list(self.opt.ema),
            "step": self.loop.step,
        }


def make(cfg, lk):
    return Ctx(cfg, lk)
