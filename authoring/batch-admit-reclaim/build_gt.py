"""Write tests/gt.json from the sealed model, and refuse if the reference differs.

Ground truth comes from oracle.py rather than from the tree, so the answers the
verifier holds were produced by the implementation that shares no code with the
thing being graded. The reference is then held to those answers; a disagreement
means one of the two is wrong and the file is not written.

Usage: python3 authoring/batch-admit-reclaim/build_gt.py
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
TESTS = os.path.join(ROOT, "tasks", "batch-admit-reclaim", "tests")
sys.path.insert(0, HERE)
sys.path.insert(0, TESTS)

import cases
import gen
import oracle
import play

WORK = os.environ.get("WORK", "/tmp/bar-work")


def main(argv):
    ref = play.reference(os.path.join(WORK, "ref"))
    truth = {}
    bad = []
    for name in sorted(cases.TRACES):
        text = cases.TRACES[name]
        want = [list(x) for x in oracle.play(text)]
        got = [list(x) for x in play.safe(ref, text)]
        if got != want:
            bad.append(name)
        truth[name] = want
    wide = int(argv[1]) if len(argv) > 1 else 400
    for name, text in gen.batch("build-gt", wide):
        want = [list(x) for x in oracle.play(text)]
        got = [list(x) for x in play.safe(ref, text)]
        if got != want:
            bad.append(name)
    if bad:
        print("reference and sealed model differ on %d: %s" % (len(bad), bad[:6]))
        return 1
    with open(os.path.join(TESTS, "gt.json"), "w") as handle:
        json.dump(truth, handle, sort_keys=True, indent=1)
        handle.write("\n")
    print("gt.json: %d enumerated traces, %d lines; agreed on %d generated traces"
          % (len(truth), sum(len(v) for v in truth.values()), wide))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
