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

overlay = None if sys.argv[1] == "ship" else pathlib.Path(sys.argv[1])
seed = sys.argv[2] if len(sys.argv) > 2 else "deadbeef"
lb = lab.Lab(overlay)
t0 = time.time()
for name in cases.ORDER:
    lb.run(cases.ops(name))
t1 = time.time()
print("hand   %.2fs" % (t1 - t0), flush=True)
by = {}
for fam, name, lines in gen.programs(seed, 45):
    t = time.time()
    lb.run(lines)
    by[fam] = by.get(fam, 0.0) + time.time() - t
for fam in sorted(by):
    print("%-6s %.2fs" % (fam, by[fam]), flush=True)
print("total  %.2fs" % (time.time() - t0), flush=True)
lb.close()
