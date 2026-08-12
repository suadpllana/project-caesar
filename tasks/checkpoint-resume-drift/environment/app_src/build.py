import json
import os

from core.ckstore import CkStore
from core.meter import Meter
from data.feed import Feed
from data.samp import Samp
from data.store import Store
from train.loop import Loop
from train.model import Model
from train.noise import Noise
from train.opt import Opt
from train.sched import Sched

PARTS = ("store", "samp", "feed", "noise", "sched", "model", "opt", "loop")


class Ctx:
    def __init__(self, cfg):
        self.cfg = cfg
        self.mt = Meter()
        self.ck = CkStore()
        self.tr = []
        self.up()

    def up(self):
        c = self.cfg
        self.store = Store(c, self.mt)
        self.samp = Samp(c, self.mt)
        self.feed = Feed()
        self.noise = Noise(c)
        self.sched = Sched(c)
        self.model = Model(c, self.mt)
        self.opt = Opt(c, self.model, self.mt)
        self.loop = Loop(self)

    def down(self):
        for nm in PARTS:
            setattr(self, nm, None)

    def amend(self, sched, top):
        for k, v in sched.items():
            self.cfg["sched"][k] = v
        for k, v in top.items():
            self.cfg[k] = v
        if self.sched is not None:
            self.sched.clear()

    def report(self):
        r = dict(self.mt.as_map())
        r["p"] = list(self.model.p)
        r["ema"] = list(self.opt.ema)
        r["step"] = self.loop.step
        r["trace"] = list(self.tr)
        return r


def load_cfg(over=None):
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "conf", "train.json")) as fh:
        cfg = json.load(fh)
    for k, v in (over or {}).items():
        if k == "sched":
            for a, b in v.items():
                cfg["sched"][a] = b
        else:
            cfg[k] = v
    return cfg


def make(over=None):
    return Ctx(load_cfg(over))
