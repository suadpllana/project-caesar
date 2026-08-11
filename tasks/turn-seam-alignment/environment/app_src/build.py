import json
import os

from loop.gen import Gen
from loop.rt import RT
from model.net import Net
from tok.core import Tok
from tok.store import Store

ROOT = os.path.dirname(os.path.abspath(__file__))
CONF = os.path.join(ROOT, "conf", "loop.json")


def load(over=None):
    with open(CONF) as f:
        cfg = json.load(f)
    if over:
        cfg.update(over)
    return cfg


def make(over=None):
    cfg = load(over)
    tok = Tok()
    net = Net()
    return RT(cfg, tok, net, Gen(net), Store(cfg["store"]))
