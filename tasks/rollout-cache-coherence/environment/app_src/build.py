import json
import os

from mem.pool import Pool
from model.be import Backend
from model.pstore import PStore
from runtime.blk import Blk
from runtime.eng import Eng
from runtime.pfx import Pfx
from runtime.sch import Sch

ROOT = os.path.dirname(os.path.abspath(__file__))
CONF = os.path.join(ROOT, "conf", "engine.json")


def load(over=None):
    with open(CONF) as f:
        cfg = json.load(f)
    if over:
        cfg.update(over)
    return cfg


def make(over=None):
    cfg = load(over)
    ps = PStore(cfg["seeds"], cfg["adapters"])
    pool = Pool(int(cfg["pages"]), int(cfg["block"]))
    blk = Blk(pool, int(cfg["block"]))
    pfx = Pfx(blk)
    blk.pfx = pfx
    sch = Sch(cfg)
    eng = Eng(cfg, ps, pool, blk, pfx, sch, Backend())
    sch.eng = eng
    return eng
