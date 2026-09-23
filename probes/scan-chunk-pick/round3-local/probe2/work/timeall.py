import os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
APP = os.path.join(os.path.dirname(HERE), "app")
sys.path.insert(0, HERE)
import gen, gen2
sys.path.insert(0, APP)
import run_scan
texts = []
for f in ["wide", "deep"]:
    t = open(os.path.join(APP, "segs", f + ".txt")).read()
    texts += [t] * 3
for s in range(154):
    texts.append(gen2.make(1000 + s, "wide"))
    texts.append(gen2.make(1000 + s, "deep"))
for s in range(60):
    texts.append(gen.make(5000 + s))
t0 = time.time()
for t in texts:
    run_scan.run(t)
print("files", len(texts), "total %.2fs" % (time.time() - t0))
