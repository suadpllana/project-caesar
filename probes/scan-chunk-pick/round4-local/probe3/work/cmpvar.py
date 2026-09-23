import os, sys, importlib
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "app")); sys.path.insert(0, HERE)
import gen, gen2, ref
v = importlib.import_module(sys.argv[1])
n = int(sys.argv[2])
for g in (gen, gen2):
    diff = 0
    for seed in range(n):
        t = g.make(seed)
        if ref.run(t) != v.run(t):
            diff += 1
    print(g.__name__, "differs in", diff, "of", n)
