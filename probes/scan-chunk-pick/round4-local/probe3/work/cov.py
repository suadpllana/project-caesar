import os, sys, trace
HERE = os.path.dirname(os.path.abspath(__file__))
APP = os.path.join(HERE, "..", "app")
sys.path.insert(0, APP); sys.path.insert(0, HERE)
import gen, gen2, run_scan
from scn import hdr, dct, live, pick, step, proj
mods = [hdr, dct, live, pick, step, proj]
t = trace.Trace(count=1, trace=0)
def work():
    for seed in range(int(sys.argv[1]), int(sys.argv[2])):
        run_scan.run(gen.make(seed)); run_scan.run(gen2.make(seed))
t.runfunc(work)
counts = t.results().counts
for m in mods:
    fn = m.__file__
    src = open(fn).read().split("\n")
    import ast
    tree = ast.parse("\n".join(src))
    lines = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.stmt) and not isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Import, ast.ImportFrom)):
            if isinstance(node, ast.Expr) and isinstance(getattr(node, 'value', None), ast.Constant):
                continue
            lines.add(node.lineno)
    miss = sorted(l for l in lines if counts.get((fn, l), 0) == 0)
    print(os.path.basename(fn), "missed:", [(l, src[l-1].strip()[:60]) for l in miss])
