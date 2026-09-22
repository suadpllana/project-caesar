"""Print the enumerated programs with the model's trace, and check brute and reference agree."""
import sys

import brute
import lab

sys.path.insert(0, str(lab.TASK / "tests"))
sys.path.insert(0, str(lab.TASK / "tests" / "seal"))
import cases  # noqa: E402
import model  # noqa: E402

run = lab.pane("solution")
names = sys.argv[1:] or cases.ORDER
bad = 0
for name in names:
    lines = cases.prog(name)
    want = model.expect(lines)
    ok_b = brute.expect(lines) == want
    ok_r = run(lines) == want
    if not (ok_b and ok_r):
        bad += 1
    print("== %s%s" % (name, "" if ok_b and ok_r else "   DISAGREE brute=%s ref=%s" % (ok_b, ok_r)))
    print("   " + " | ".join(lines))
    for ln in want:
        print("   " + ln)
print("disagreements:", bad)
