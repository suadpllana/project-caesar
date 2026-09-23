"""The sealed model against the plain stepper on one generated family, over many seeds.

usage: python3 authoring/stale-line-spin/agree_fam.py <family> <seeds> [mode ...]
"""
import collections
import random
import sys
import time

sys.path.insert(0, "tasks/stale-line-spin/tests/seal")
sys.path.insert(0, "tasks/stale-line-spin/tests")
sys.path.insert(0, "authoring/stale-line-spin")
import gen  # noqa: E402
import model  # noqa: E402
import naive  # noqa: E402

fam = sys.argv[1]
seeds = int(sys.argv[2])
modes = sys.argv[3:] or ["local"]
bad = 0
kinds = collections.Counter()
t0 = time.time()
for i in range(seeds):
    lines = gen.GEN[fam](random.Random("agree:%s:%d" % (fam, i)))
    want = naive.run(lines)
    kinds["hang" if any(x.startswith("hang") for x in want) else "ends"] += 1
    for mode in modes:
        if model.expect(lines, mode) != want:
            bad += 1
            if bad <= 2:
                print("DIFFER", fam, i, mode)
                print("\n".join(lines))
print("%s: %d launches x %d modes, %d disagreements, %s, %.1fs" % (
    fam, seeds, len(modes), bad, dict(kinds), time.time() - t0))
