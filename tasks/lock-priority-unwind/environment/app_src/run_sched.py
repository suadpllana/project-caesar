import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rt import boot, prio


def load(path):
    with open(path) as fh:
        return json.load(fh)


def main(argv):
    if len(argv) < 2:
        print("usage: run_sched.py <scenario.json>")
        return 2
    sc = load(argv[1])
    base = load(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "conf", "sched.json"))
    cfg = dict(base)
    for k, v in (sc.get("cfg") or {}).items():
        cfg[k] = v
    c = boot.build(cfg, sc)
    c.bind(prio.Prio(c))
    c.run(cfg["limit"])
    print(json.dumps(c.report(), indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
