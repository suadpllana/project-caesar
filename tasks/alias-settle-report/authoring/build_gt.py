"""Write tests/gt.json, and refuse to write one that has not been proved.

Ground truth is the sealed model's answer, never the reference's, and it is only
written once the two have been held against each other on random sets. A ground
truth taken from the implementation under examination proves nothing about the
implementation.
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(TASK, "tests"))

import cases
import fuzz
import harness
import oracle

OUT = os.path.join(TASK, "tests", "gt.json")


def main(argv):
    rounds = int(argv[1]) if len(argv) > 1 else 900
    bad, spent = fuzz.run(rounds, "gt")
    if bad:
        print("refusing to write ground truth: reference and model disagree")
        print(bad[0])
        return 1
    print("reference == model on %d generated sets (%.1fs)" % (rounds, spent))

    rig = harness.Rig(os.path.join(TASK, "solution"))
    truth = {}
    split = []
    for name in sorted(cases.SETS):
        text = cases.SETS[name]
        want = oracle.play(text)
        if rig.run(text) != want:
            split.append(name)
        truth[name] = want
    rig.close()
    if split:
        print("refusing to write ground truth: they disagree on %s" % split)
        return 1

    with open(OUT, "w", newline="\n") as fh:
        json.dump(truth, fh, sort_keys=True, indent=1)
        fh.write("\n")
    os.chmod(OUT, 0o600)
    print("wrote %s: %d enumerated sets" % (OUT, len(truth)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
