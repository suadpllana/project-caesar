import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
TESTS = pathlib.Path(__file__).resolve().parents[2] / "tasks" / "publish-settle-order" / "tests"
sys.path.insert(0, str(TESTS))
sys.path.insert(0, str(TESTS / "seal"))
import gen  # noqa: E402
import lab  # noqa: E402

which = sys.argv[1]
overlay = None if which == "ship" else pathlib.Path(sys.argv[1])
lb = lab.Lab(overlay)
seed = sys.argv[2] if len(sys.argv) > 2 else "deadbeef"
progs = [p for p in gen.programs(seed, 60) if p[0] == "wide"]
t0 = time.time()
for fam, name, lines in progs:
    t = time.time()
    out = lb.run(lines)
    print("%s %d lines -> %d events  %.2fs" % (name, len(lines), len(out), time.time() - t), flush=True)
print("total %.2fs" % (time.time() - t0), flush=True)
lb.close()
