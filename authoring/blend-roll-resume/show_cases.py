"""Print every enumerated case with the three engines' answers, so they can be read."""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
TASK = ROOT / "tasks" / "blend-roll-resume"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(TASK / "tests"))
sys.path.insert(0, str(TASK / "tests" / "seal"))

import cases  # noqa: E402
import lab  # noqa: E402
import model  # noqa: E402
import naive  # noqa: E402

REF = TASK / "solution"


def main():
    only = sys.argv[1:] or cases.ORDER
    bad = 0
    for name in only:
        lines = cases.ops(name)
        want = model.expect(lines)
        ref = lab.inproc(lines, REF)
        nv = naive.expect(lines)
        ship = lab.inproc(lines, None)
        mark = "" if (ref == want == nv) else "   *** DISAGREE ***"
        if mark:
            bad += 1
        print("== %s%s" % (name, mark))
        for line in lines:
            print("   |", line)
        for line in want:
            print("   ->", line)
        if ref != want:
            print("   ref:", ref)
        if nv != want:
            print("   naive:", nv)
        print("   shipped differs: %s" % (ship != want))
        print()
    print("disagreements:", bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
