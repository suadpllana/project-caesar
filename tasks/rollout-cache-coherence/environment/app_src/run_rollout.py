import json
import sys

import build
from runtime.drv import play

DEFAULT = {
    "over": {"pages": 64},
    "ops": [
        {"op": "add", "rid": "r0", "prompt": [5, 9, 14, 3, 21, 7, 2, 11], "adapter": None, "max_new": 6},
        {"op": "add", "rid": "r1", "prompt": [5, 9, 14, 3, 21, 7, 2, 11], "adapter": None, "max_new": 6},
        {"op": "step", "n": 3},
        {"op": "sync", "ups": [[None, "l1.wk", 9001]]},
        {"op": "drain"},
    ],
}


def main(argv):
    if len(argv) > 1:
        with open(argv[1]) as f:
            spec = json.load(f)
    else:
        spec = DEFAULT
    eng = build.make(spec.get("over"))
    rep = play(eng, spec["ops"])
    print(json.dumps(rep, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
