"""Every alternative correct implementation must score 1 through the real verifier.

This is the cheat suite's mirror image and it is the gate the run audit actually applies:
a graded quantity that two correct implementations disagree on is a trap, not a test. The
variants differ in how they compute the window, how they express the resting rule, how
they build the band's ordering, and in one case they do something provably unobservable
(clearing a mark on a guard that has already left every chain) to prove the verifier is
not grading the shape of the code.
"""

import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    vd = os.path.join(HERE, "variants")
    bad = 0
    for name in sorted(os.listdir(vd)):
        p = os.path.join(vd, name)
        if not os.path.isdir(p):
            continue
        rc = subprocess.run([sys.executable, os.path.join(HERE, "trial.py"),
                             "--dir", p], capture_output=True, text=True)
        line = rc.stdout.strip().splitlines()[0] if rc.stdout.strip() else "no output"
        print(line)
        if "reward 1" not in line:
            bad += 1
    print("%s" % ("all variants accepted" if not bad else "%d VARIANTS REJECTED" % bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
