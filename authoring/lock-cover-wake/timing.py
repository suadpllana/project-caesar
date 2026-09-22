#!/usr/bin/env python3
"""Time the reference and the correct-but-slow readings on the scale families. Never ships.

    python3 -u authoring/lock-cover-wake/timing.py [seed] [--fam wide,deep] [--cut 300]

Prints seconds per script and says whether each reading agrees with the reference on whatever
it finishes. The execution limit in the brief is for the whole graded set, so a reading that
needs more than that on one script is out whatever else it gets right.
"""
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402

cases, gen, model = lab.sealed()

SLOW = ("wake", "tally", "stand")


def main():
    argv = sys.argv[1:]
    fams = ["wide", "deep"]
    cut = 400
    if "--fam" in argv:
        i = argv.index("--fam")
        fams = argv[i + 1].split(",")
        del argv[i:i + 2]
    if "--cut" in argv:
        i = argv.index("--cut")
        cut = int(argv[i + 1])
        del argv[i:i + 2]
    seed = argv[0] if argv else "time"

    work = [w for w in gen.programs(seed, 1) if w[0] in fams]
    trees = {"reference": lab.tree(policy=str(lab.SOL))}
    for name in SLOW:
        trees[name] = lab.tree(policy=str(HERE / "slow" / name))

    for fam, name, lines in work:
        text = "\n".join(lines) + "\n"
        print("== %s  (%d lines)" % (name, len(lines)))
        want = None
        for who in ("reference",) + SLOW:
            t0 = time.time()
            got = lab.run_shell(trees[who], text, timeout=cut)
            secs = time.time() - t0
            if who == "reference":
                want = got
                print("   %-10s %7.2fs  %d lines out" % (who, secs, len(got)))
            elif got == ["TIMEOUT"]:
                print("   %-10s  over %ds" % (who, cut))
            else:
                print("   %-10s %7.2fs  %s" % (who, secs,
                                               "same answer" if got == want else "DIFFERS"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
