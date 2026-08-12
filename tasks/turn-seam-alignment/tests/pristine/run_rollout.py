import json
import sys

import build
from loop.drv import play

DEFAULT = {
    "over": {},
    "ops": [
        {"op": "begin", "ep": "e0", "salt": 7717},
        {"op": "user", "ep": "e0", "text": "check the stale queue for #q4821"},
        {"op": "turn", "ep": "e0", "cap": 24},
        {"op": "tool", "ep": "e0", "text": "status=ok items=12 @w/ingest"},
        {"op": "turn", "ep": "e0", "cap": 24},
        {"op": "end", "ep": "e0"},
    ],
}


def main(argv):
    if len(argv) > 1:
        with open(argv[1]) as f:
            spec = json.load(f)
    else:
        spec = DEFAULT
    rt = build.make(spec.get("over"))
    rep = play(rt, spec["ops"])
    print(json.dumps(rep, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
