"""Run every alternative correct implementation through the same checks the verifier applies.

A variant that follows the contract and scores 0 means the verifier is grading an
implementation choice rather than a behaviour, which is a defect in the verifier, not in the
variant.

    python3 authoring/space-charge-shift/variant_check.py [per]
"""
import json
import os
import sys
import time

import harness

sys.path.insert(0, harness.TESTS)
import cases  # noqa: E402
import gen  # noqa: E402
import model  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
GT = json.load(open(os.path.join(harness.TESTS, "gt.json")))


def check(tree, per):
    for name in cases.ORDER:
        got = harness.run(tree, cases.ops(name))
        if got != GT[name]:
            first = [(a, b) for a, b in zip(got, GT[name]) if a != b][:1]
            return "hand %s %s" % (name, first)
    for fam, name, lines in gen.programs("variantprobe", per):
        script = gen.ops(lines)
        got = harness.run(tree, script)
        if got != model.run(script):
            return "%s %s" % (fam, name)
    return None


def main(argv):
    per = int(argv[1]) if len(argv) > 1 else 6
    home = os.path.join(HERE, "variants")
    bad = 0
    for name in sorted(os.listdir(home)):
        d = os.path.join(home, name)
        if not os.path.isdir(d):
            continue
        tree = harness.tree(policy=d)
        t0 = time.time()
        why = check(tree, per)
        print("  %-18s %s   (%.1fs)" % (name, why or "scores 1 on every script", time.time() - t0))
        bad += why is not None
    print("%d variants, %d failing" % (len(os.listdir(home)), bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
