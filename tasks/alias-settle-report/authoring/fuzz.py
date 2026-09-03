"""Hold the reference against the sealed model on sets nobody wrote by hand.

The reference argues that looking at each cell that could still be welded on, one
at a time, is enough. The model makes no such argument: it walks the groups a
legal future could actually build. If the argument is wrong anywhere, the two
part, and this is where that shows up rather than in a probe.
"""

import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(TASK, "tests"))

import gen
import harness
import oracle


def run(rounds, tag="fuzz"):
    rig = harness.Rig(os.path.join(TASK, "solution"))
    bad = []
    clock = time.time()
    for i in range(rounds):
        text = gen.one("%s:%d" % (tag, i))
        if rig.run(text) != oracle.play(text):
            bad.append(text)
            if len(bad) > 3:
                break
    rig.close()
    return bad, time.time() - clock


def main(argv):
    rounds = int(argv[1]) if len(argv) > 1 else 800
    bad, spent = run(rounds)
    if bad:
        print("the reference and the model disagree on %d sets" % len(bad))
        print(bad[0])
        return 1
    print("reference == model on %d sets (%.1fs)" % (rounds, spent))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
