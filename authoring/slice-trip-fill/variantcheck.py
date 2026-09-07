"""Every alternative correct implementation must agree with the reference, event for event."""

import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gen
import readings

ART = ("take.py", "shown.py", "hand.py", "hold.py", "trip.py")


def blend(vdir):
    d = tempfile.mkdtemp(prefix="var-")
    for fn in ART:
        shutil.copyfile(os.path.join(readings.REFERENCE, fn), os.path.join(d, fn))
    for fn in os.listdir(vdir):
        if fn.endswith(".py"):
            shutil.copyfile(os.path.join(vdir, fn), os.path.join(d, fn))
    return d


def main(argv):
    n = int(argv[1]) if len(argv) > 1 else 400
    pop = list(readings.enumerated()) + gen.batch("variantcheck", n) \
        + gen.deep_batch("variantcheck", 1)
    want = {nm: readings.run(readings.REFERENCE, t) for nm, t in pop}
    root = os.path.join(HERE, "variants")
    bad = 0
    for name in sorted(os.listdir(root)):
        d = blend(os.path.join(root, name))
        wrong = []
        for nm, t in pop:
            try:
                got = readings.run(d, t)
            except Exception as exc:
                wrong.append("%s raised %r" % (nm, exc))
                continue
            if got != want[nm]:
                for i in range(max(len(got), len(want[nm]))):
                    a = got[i] if i < len(got) else None
                    b = want[nm][i] if i < len(want[nm]) else None
                    if a != b:
                        wrong.append("%s event %d %s != %s" % (nm, i, a, b))
                        break
        if wrong:
            bad += 1
            print("%-20s DISAGREES on %d of %d\n    %s"
                  % (name, len(wrong), len(pop), "\n    ".join(wrong[:3])))
        else:
            print("%-20s agrees on all %d sessions" % (name, len(pop)))
    return 1 if bad else 0
if __name__ == "__main__":
    sys.exit(main(sys.argv))
