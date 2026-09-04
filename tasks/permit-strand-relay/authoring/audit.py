"""Totality audit: on the enumerated states, does the reference agree with the
sealed model and with every alternative construction, and does each state
actually exercise something?"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "tests"))

import cases
import harness
import oracle


def main():
    plans = [cases.SETS[k] for k in sorted(cases.SETS)]
    base = harness.drive(plans, os.path.join(ROOT, "solution"))
    if "__fault__" in base:
        print(base["__fault__"])
        return 1
    bad = 0
    print("%-20s %5s %5s %5s %5s %5s  %s"
          % ("case", "rows", "gr", "pull", "over", "late", "model"))
    for plan in plans:
        name = plan["name"]
        mine = base[name]
        if "error" in mine:
            print("%-20s REFERENCE RAISED %s" % (name, mine["error"]))
            bad += 1
            continue
        rows, park = oracle.settle(plan)
        ok = (mine["ev"] == rows
              and mine["park"] == dict((str(k), v) for k, v in park.items()))
        kinds = dict()
        for row in mine["ev"]:
            kinds[row[0]] = kinds.get(row[0], 0) + 1
        print("%-20s %5d %5d %5d %5d %5d  %s"
              % (name, len(mine["ev"]), kinds.get("grant", 0),
                 kinds.get("pull", 0), kinds.get("over", 0),
                 kinds.get("late", 0), "agrees" if ok else "DISAGREES"))
        if not ok:
            bad += 1
    home = os.path.join(HERE, "variants")
    for leaf in sorted(os.listdir(home)):
        got = harness.drive(plans, os.path.join(home, leaf))
        off = [p["name"] for p in plans if got.get(p["name"]) != base.get(p["name"])]
        print("variant %-16s %s %s" % (leaf, "agrees" if not off else "DIFFERS", off[:3]))
        if off:
            bad += 1
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
