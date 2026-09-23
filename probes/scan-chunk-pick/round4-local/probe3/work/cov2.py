import os, sys, trace
HERE = os.path.dirname(os.path.abspath(__file__))
APP = os.path.join(HERE, "..", "app")
sys.path.insert(0, APP); sys.path.insert(0, HERE)
import run_scan
from scn import pick
t = trace.Trace(count=1, trace=0)
def work():
    for f in sys.argv[1:]:
        run_scan.run(open(f).read())
t.runfunc(work)
counts = t.results().counts
fn = pick.__file__
src = open(fn).read().split("\n")
for l in range(38, 50):
    print(l, counts.get((fn, l), 0), src[l-1])
