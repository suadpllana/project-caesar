import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "app"))
import shaped, model, run_scan
a, b = int(sys.argv[1]), int(sys.argv[2])
bad = 0
nlines = 0
for seed in range(a, b):
    text = shaped.make(seed)
    want = model.run(text)
    got = run_scan.run(text)
    nlines += len(want)
    if want != got:
        bad += 1
        print("DIFF", seed)
        open(os.path.join(HERE, "sfail_%d.txt" % seed), "w", newline="\n").write(text)
print("done", b - a, "bad", bad, "lines", nlines)
