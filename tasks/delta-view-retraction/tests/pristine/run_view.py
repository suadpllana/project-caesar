import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from view import drv


def load(path):
    with open(path) as fh:
        return json.load(fh)


def main(argv):
    if len(argv) < 2:
        print("usage: run_view.py <scenario.json>")
        return 2
    sc = load(argv[1])
    base = load(os.path.join(os.path.dirname(os.path.abspath(__file__)), "conf", "view.json"))
    cfg = dict(base)
    for k, v in (sc.get("cfg") or {}).items():
        cfg[k] = v
    d = drv.Drv(cfg)
    rep = d.run(sc["ops"])
    print(json.dumps(rep, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
