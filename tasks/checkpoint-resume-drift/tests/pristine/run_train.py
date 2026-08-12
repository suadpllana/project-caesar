import json
import os
import sys

import build
from train import drv


def main(argv):
    here = os.path.dirname(os.path.abspath(__file__))
    path = argv[1] if len(argv) > 1 else os.path.join(here, "conf", "demo.json")
    with open(path) as fh:
        sc = json.load(fh)
    cx = build.make(sc.get("over"))
    rep = drv.play(cx, sc["ops"])
    print(json.dumps(rep, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
