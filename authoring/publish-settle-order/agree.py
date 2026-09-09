"""Differential check: the reference and the sealed model must agree everywhere."""
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
TESTS = pathlib.Path(__file__).resolve().parents[2] / "tasks" / "publish-settle-order" / "tests"
sys.path.insert(0, str(TESTS))
sys.path.insert(0, str(TESTS / "seal"))
import cases  # noqa: E402
import gen  # noqa: E402
import lab  # noqa: E402
import model  # noqa: E402

seed = sys.argv[1] if len(sys.argv) > 1 else "deadbeef"
per = int(sys.argv[2]) if len(sys.argv) > 2 else 60
lb = lab.Lab(lab.TASK / "solution")
bad = 0
for name in cases.ORDER:
    got, want = lb.run(cases.ops(name)), model.expect(cases.ops(name))
    if got != want:
        bad += 1
        print("HAND %s\n  ref  %s\n  mod  %s" % (name, got, want))
t0 = time.time()
for fam, name, lines in gen.programs(seed, per):
    got, want = lb.run(lines), model.expect(lines)
    if got != want:
        bad += 1
        if bad < 5:
            n = min(len(got), len(want))
            at = next((i for i in range(n) if got[i] != want[i]), n)
            print("GEN %s at %d\n  ref  %s\n  mod  %s" % (name, at, got[at:at + 3], want[at:at + 3]))
print("%d disagreements, %.1fs" % (bad, time.time() - t0))
lb.close()
