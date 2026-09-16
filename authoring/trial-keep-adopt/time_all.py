"""How long the graded set takes, by family, through the reference and through the model."""
import sys
import time

import lab

TASK = lab.TASK
sys.path.insert(0, str(TASK / "tests"))
sys.path.insert(0, str(TASK / "tests" / "seal"))
import gen      # noqa: E402
import model    # noqa: E402

per = int(sys.argv[1]) if len(sys.argv) > 1 else 40
which = sys.argv[2] if len(sys.argv) > 2 else "ref"
here = lab.ref()
ops, prog, store = lab.load(here)
by = {}
t00 = time.time()
for fam, name, lines in gen.programs("time", per):
    t0 = time.time()
    if which == "ref":
        f = store.Fld()
        for w in prog.walk(lines):
            ops.ex(f, w)
        n = len(f.out)
    else:
        n = len(model.expect(lines))
    d = time.time() - t0
    a, b, c = by.get(fam, (0, 0.0, 0))
    by[fam] = (a + 1, b + d, c + n)
for fam in by:
    print("%-8s %3d programs %8.2fs %9d lines" % (fam, by[fam][0], by[fam][1], by[fam][2]),
          flush=True)
print("total %.2fs" % (time.time() - t00))
