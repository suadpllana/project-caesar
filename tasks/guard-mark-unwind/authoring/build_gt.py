"""Write tests/gt.json, and refuse to write it without proving it first.

gt.json is a tripwire rather than an answer key: the randomized set is graded against
oracle.py live, so what this file records is only the enumerated set, and the verifier
requires the model to still reproduce it. Two things are proved before it is written.

  The reference tree and the sealed model agree, event for event, on every enumerated case
  and on several thousand random programs. They are independent implementations, so
  agreement at that scale is evidence about the specification rather than about a shared
  bug - and it is the same comparison the verifier makes at trial time, so a disagreement
  here is a task that is unfair in whichever direction it leans.

  The shipped tree does NOT agree, on a healthy fraction of the same programs. A ground
  truth the broken tree already satisfies would grade nothing.
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
from fuzz import norm

ROUNDS = 3000


def main(argv):
    ref = harness.tree(os.path.join(ROOT, "solution"))
    ship = harness.tree()
    pool = [(nm, cases.PROGS[nm]) for nm in sorted(cases.PROGS)]
    pool += [(nm, gen.text(p)) for nm, p in gen.batch("build", ROUNDS)]

    drift = []
    caught = 0
    for name, text in pool:
        want = norm(oracle.solve(text))
        if norm(harness.run(ref, text)) != want:
            drift.append(name)
        if norm(harness.safe(ship, text)) != want:
            caught += 1
    if drift:
        print("reference and model disagree on %d programs: %s"
              % (len(drift), drift[:5]))
        return 1
    share = 100.0 * caught / len(pool)
    print("reference agrees with the model on all %d programs" % len(pool))
    print("shipped tree disagrees on %d (%.1f%%)" % (caught, share))
    if share < 20.0:
        print("the shipped tree is too close to correct to grade")
        return 1

    out = {"cases": {}, "notes": {}}
    for name in sorted(cases.PROGS):
        res = oracle.solve(cases.PROGS[name])
        out["cases"][name] = {
            "tr": [list(r) for r in res["tr"]],
            "tk": [[a, b, list(c)] for a, b, c in res["tk"]],
        }
        out["notes"][name] = cases.NOTE[name]
    path = os.path.join(ROOT, "tests", "gt.json")
    with open(path, "w", newline="\n") as fh:
        json.dump(out, fh, indent=1, sort_keys=True)
        fh.write("\n")
    print("wrote %s (%d cases)" % (path, len(out["cases"])))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
