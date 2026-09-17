"""The correct-but-rebuilding service against the limit, on the two scale families."""
import random
import sys
import pathlib
import time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent.parent / "tasks/queue-hold-drop/tests"))
import gen  # noqa: E402
import lab  # noqa: E402

for fam in ("wide", "deep"):
    r = random.Random("scale|%s|0" % fam)
    lines = gen.build(fam, r, small=False)
    for tree in ("ref", "slow"):
        t0 = time.time()
        lab.run(lines, tree)
        print("%-5s %-5s %6d lines  %8.1f s" % (fam, tree, len(lines), time.time() - t0), flush=True)
