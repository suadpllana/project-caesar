"""Differential fuzz: the reference tree against the sealed model.

Two independent implementations of one specification, run over the hand cases and the
generated families and compared line for line. build_gt.py refuses to write a ground truth
without a clean run of this: the verifier grades the generated set against the model live, so a
disagreement makes the task unfair in whichever direction it points.

    python3 authoring/space-charge-shift/fuzz.py [per] [seed]
"""
import sys
import time

import harness

sys.path.insert(0, harness.TESTS)
import cases  # noqa: E402
import gen  # noqa: E402
import model  # noqa: E402


def main(argv):
    per = int(argv[1]) if len(argv) > 1 else 20
    seed = argv[2] if len(argv) > 2 else "fuzz"
    dst = harness.tree(policy=harness.TASK + "/solution")
    pool = [("hand", nm, cases.CASES[nm]) for nm in cases.ORDER]
    pool += gen.programs(seed, per)
    bad = 0
    t0 = time.time()
    for fam, nm, lines in pool:
        script = gen.ops(lines)
        want = model.run(script)
        got = harness.run(dst, script)
        if got != want:
            bad += 1
            print("MISMATCH %s %s" % (fam, nm))
            for j, (a, b) in enumerate(zip(got, want)):
                if a != b:
                    print("   line %d: ref %-24s model %s" % (j, a, b))
                    break
            if len(got) != len(want):
                print("   lengths %d %d" % (len(got), len(want)))
            if bad > 4:
                break
    print("%d scripts, %d mismatches, %.1fs" % (len(pool), bad, time.time() - t0))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
