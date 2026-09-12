"""Time one implementation on one program of one family, with the clock flushed."""
import pathlib, sys, time
HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parent.parent / "tasks" / "claim-line-stall"
sys.path.insert(0, str(TASK / "tests")); sys.path.insert(0, str(HERE))
import gen, lab

over, fam = sys.argv[1], sys.argv[2]
here = lab.stage(over); sys.path.insert(0, str(here))
import ops
from hold import book as bk
_f, name, lines = [p for p in gen.programs("timing-seed", 1) if p[0] == fam][0]
h = bk.Hold(); t0 = time.time()
for line in lines:
    ops.ex(h, tuple(line.split()))
print("%-24s %-5s %7.2f s  %d ops" % (over.split("/")[-1], fam, time.time() - t0, len(lines)), flush=True)
