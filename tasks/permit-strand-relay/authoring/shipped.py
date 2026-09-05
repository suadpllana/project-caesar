"""How much of the graded set the shipped tree already gets right."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(ROOT, "tests"))
import cases, gen, harness

fixed = [cases.SETS[k] for k in sorted(cases.SETS)]
streams = gen.small(31337, 300)
ref_f = harness.drive(fixed, os.path.join(ROOT, "solution"))
ref_g = harness.drive(streams, os.path.join(ROOT, "solution"))
shp_f = harness.drive(fixed)
shp_g = harness.drive(streams)
okf = [p["name"] for p in fixed if shp_f.get(p["name"]) == ref_f.get(p["name"])]
okg = [p["name"] for p in streams if shp_g.get(p["name"]) == ref_g.get(p["name"])]
print("shipped tree passes %d of %d enumerated: %s" % (len(okf), len(fixed), ", ".join(okf)))
print("shipped tree passes %d of %d generated" % (len(okg), len(streams)))
