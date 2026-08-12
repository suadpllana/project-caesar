import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core import conf
from train import drv


def main(argv):
    here = os.path.dirname(os.path.abspath(__file__))
    path = argv[1] if len(argv) > 1 else os.path.join(here, "conf", "demo.json")
    with open(path) as fh:
        sc = json.load(fh)
    cfg = conf.merge(conf.base(here), sc.get("over"))
    ds = conf.corpus(os.environ.get("CORPUS") or os.path.join(here, "conf", "corpus.json"))
    rep = drv.play(cfg, sc["ops"], ds)
    rep.pop("lives", None)
    print(json.dumps(rep, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
