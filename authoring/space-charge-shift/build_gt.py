"""Freeze the hand-case ground truth from the sealed model.

Refuses to write anything until the differential fuzz is clean, because the file it writes is
what the verifier compares hand cases against: a ground truth derived from a model that
disagrees with the reference is a task that grades the wrong answer.

    python3 authoring/space-charge-shift/build_gt.py [per] [seed]
"""
import json
import os
import sys

import fuzz
import harness

sys.path.insert(0, harness.TESTS)
import cases  # noqa: E402
import model  # noqa: E402

OUT = os.path.join(harness.TESTS, "gt.json")


def main(argv):
    if fuzz.main(["fuzz"] + argv[1:]) != 0:
        print("fuzz is not clean - refusing to freeze a ground truth")
        return 1
    truth = dict((nm, model.run(cases.ops(nm))) for nm in cases.ORDER)
    with open(OUT, "w", newline="\n", encoding="utf-8") as fh:
        fh.write(json.dumps(truth, indent=1, sort_keys=True))
        fh.write("\n")
    body = open(OUT, encoding="utf-8").read()
    assert "\r" not in body, "gt.json picked up a carriage return"
    print("wrote %s (%d cases, %d bytes)" % (OUT, len(truth), len(body)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
