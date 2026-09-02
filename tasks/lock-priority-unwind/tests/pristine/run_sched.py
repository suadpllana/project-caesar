import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rt import boot, prio


def load(path):
    with open(path) as fh:
        return json.load(fh)


def show(rep):
    out = ["{"]
    keys = sorted(rep)
    for i, k in enumerate(keys):
        v = rep[k]
        tail = "," if i < len(keys) - 1 else ""
        if isinstance(v, list) and v and isinstance(v[0], list):
            body = ",\n  ".join([json.dumps(x) for x in v])
            out.append(' "%s": [\n  %s\n ]%s' % (k, body, tail))
        else:
            out.append(' "%s": %s%s' % (k, json.dumps(v), tail))
    out.append("}")
    return "\n".join(out)


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
    print(show(c.report()))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
