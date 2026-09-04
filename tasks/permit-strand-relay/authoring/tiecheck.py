"""No graded value may come down to a choice the submission made freely.

Two things are checked. The machine sorts what the policy hands it before any
row is appended, so the only way sort order could decide anything is if one
tick carried two rows for the same level - then "grant" against "pull" would
break the tie and a correct implementation that produced them in the other
order would disagree. That state must never occur. And a policy has to invent
names for whatever it keeps between ticks, so the mirror variant renames every
one of them and must reach the same rows.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "tests"))

import cases
import gen
import harness


def main():
    wide = int(sys.argv[1]) if len(sys.argv) > 1 else 400
    streams = [cases.SETS[k] for k in sorted(cases.SETS)] + gen.batch(5150, wide)
    got = harness.drive(streams, os.path.join(ROOT, "solution"))
    if "__fault__" in got:
        print(got["__fault__"])
        return 1
    clash = 0
    rows = 0
    for plan in streams:
        seen = {}
        for row in got[plan["name"]]["ev"]:
            if row[0] not in ("grant", "pull"):
                continue
            rows += 1
            key = (row[1], row[2])
            if key in seen:
                clash += 1
                if clash <= 3:
                    print("%s tick %s level %s carries %s and %s"
                          % (plan["name"], row[1], row[2], seen[key], row[0]))
            seen[key] = row[0]
    print("%d streams, %d published rows, %d ticks carrying two rows for one level"
          % (len(streams), rows, clash))
    mirror = os.path.join(HERE, "variants", "ok-renamed")
    if not os.path.isdir(mirror):
        print("no ok-renamed mirror variant")
        return 1
    other = harness.drive(streams, mirror)
    off = [p["name"] for p in streams if other.get(p["name"]) != got.get(p["name"])]
    print("mirror variant: %s" % ("agrees" if not off else "DIFFERS on %s" % off[:3]))
    return 1 if clash or off else 0


if __name__ == "__main__":
    sys.exit(main())
