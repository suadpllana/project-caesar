"""Every alternative correct implementation must score 1, on the host, fast.

The real check is tools/docker_trial2.py --variants, which drives them through
the shipped verifier. This is the cheap one: drive each variant over the
enumerated sets and a block of generated ones and require row-for-row agreement
with the sealed model. A variant that parts from the model here is either a
correct reading the environment left undecided - which is a defect in the
instruction, not in the variant - or a variant that is simply wrong.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(TASK, "tests"))

import cases
import gen
import harness
import oracle

BOX = os.path.join(HERE, "variants")


def main(argv):
    rounds = int(argv[1]) if len(argv) > 1 else 300
    made = [gen.one("var:%d" % i) for i in range(rounds)]
    want_enum = dict((n, oracle.play(t)) for n, t in cases.SETS.items())
    want_made = [oracle.play(t) for t in made]
    bad = 0
    for name in sorted(os.listdir(BOX)):
        home = os.path.join(BOX, name)
        if not os.path.isdir(home) or not name.startswith("ok-"):
            continue
        rig = harness.Rig(home)
        off = [n for n in sorted(cases.SETS)
               if rig.run(cases.SETS[n]) != want_enum[n]]
        gone = sum(1 for t, w in zip(made, want_made) if rig.run(t) != w)
        rig.close()
        state = "1" if not off and not gone else "0"
        print("%-20s scores %s   enumerated off: %-24s generated off: %d"
              % (name, state, ", ".join(off[:3]) or "-", gone))
        bad += state == "0"
    print("%s" % ("every variant scores 1" if not bad else "%d variants failed" % bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
