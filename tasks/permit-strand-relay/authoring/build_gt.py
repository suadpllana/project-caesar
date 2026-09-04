"""Write tests/gt.json, and refuse to write it unproven.

The reference has to agree with the sealed model on every enumerated stream and
on a large generated sample before anything is recorded. A ground truth written
from one implementation is a record of that implementation's taste; written only
after two disjoint ones agree, it is a record of the rules.
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "tests"))

import cases
import gen
import harness
import oracle

WIDE = 400


def main():
    fixed = [cases.SETS[k] for k in sorted(cases.SETS)]
    wide = gen.batch(20260904, WIDE)
    ref = harness.drive(fixed + wide, os.path.join(ROOT, "solution"))
    if "__fault__" in ref:
        print("reference fault\n" + ref["__fault__"])
        return 1
    off = 0
    for plan in fixed + wide:
        mine = ref.get(plan["name"], {})
        if "error" in mine:
            print("%s: reference raised %s" % (plan["name"], mine["error"][:200]))
            off += 1
            continue
        rows, park = oracle.settle(plan)
        if mine["ev"] != rows or mine["park"] != dict(
                (str(k), v) for k, v in park.items()):
            print("%s: reference and sealed model disagree" % plan["name"])
            off += 1
    if off:
        print("REFUSING to write ground truth: %d disagreement(s)" % off)
        return 1
    truth = {}
    for plan in fixed:
        truth[plan["name"]] = ref[plan["name"]]
    out = os.path.join(ROOT, "tests", "gt.json")
    with open(out, "w", newline="\n") as fh:
        fh.write(json.dumps(truth, sort_keys=True, separators=(",", ":")))
    print("proved on %d enumerated and %d generated streams; wrote %d answers"
          % (len(fixed), len(wide), len(truth)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
