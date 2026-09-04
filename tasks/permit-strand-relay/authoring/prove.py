"""The reference against the sealed model, on generated streams.

A disagreement here is never a bug in one of them to be patched: it is a rule
the specification did not decide, and it is fixed in the rules before either
implementation moves.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "tests"))

import gen
import harness
import oracle


def main():
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 300
    nonce = int(sys.argv[2]) if len(sys.argv) > 2 else 4242
    streams = gen.batch(nonce, count)
    got = harness.drive(streams, os.path.join(ROOT, "solution"))
    if "__fault__" in got:
        print("HARNESS FAULT\n" + got["__fault__"])
        return 1
    bad = 0
    for plan in streams:
        name = plan["name"]
        mine = got.get(name, {})
        if "error" in mine:
            print("%s reference raised %s" % (name, mine["error"]))
            bad += 1
            continue
        rows, park = oracle.settle(plan)
        theirs = {"ev": rows, "park": dict((str(k), v) for k, v in park.items())}
        if mine["ev"] != theirs["ev"] or mine["park"] != theirs["park"]:
            bad += 1
            if bad <= 3:
                print("=== %s ===" % name)
                for i, (a, b) in enumerate(zip(mine["ev"], theirs["ev"])):
                    if a != b:
                        print("  row %d ref=%s model=%s" % (i, a, b))
                        break
                if len(mine["ev"]) != len(theirs["ev"]):
                    print("  lengths ref=%d model=%d"
                          % (len(mine["ev"]), len(theirs["ev"])))
                if mine["park"] != theirs["park"]:
                    print("  park ref=%s model=%s" % (mine["park"], theirs["park"]))
    print("%d streams, %d disagreements" % (len(streams), bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
