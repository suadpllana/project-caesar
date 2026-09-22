"""How much of the generated population does each wrong reading move, and where is the
smallest session that separates it? Writes readings/report.json."""
import json
import os
import random
import sys

from lab import forge, HERE
import bench
import fastbench
import readings as make_readings

N = int(sys.argv[1]) if len(sys.argv) > 1 else 400
rng = random.Random(4242)
sess = [forge.session(f, rng) for f in forge.FAMILIES for _ in range(N)]
size = lambda s: len(s["image"].splitlines()) + 3 * len(s["cmds"])
report = {}
for name in make_readings.READINGS:
    res = fastbench.run(os.path.join(HERE, "readings", name), sess)
    bad = bench.compare(sess, res)
    fam = {}
    for i in bad:
        fam[sess[i]["family"]] = fam.get(sess[i]["family"], 0) + 1
    smallest = min(bad, key=lambda i: size(sess[i])) if bad else None
    report[name] = {"moved": len(bad), "of": len(sess), "pct": round(100.0 * len(bad) / len(sess), 1),
                    "by_family": fam, "smallest": smallest,
                    "smallest_size": size(sess[smallest]) if smallest is not None else None}
    print("%-26s %5.1f%%  %s" % (name, report[name]["pct"], fam), flush=True)
json.dump({"report": report, "sessions": [sess[r["smallest"]] if r["smallest"] is not None else None
                                          for r in report.values()], "names": list(report)},
          open(os.path.join(HERE, "readings", "report.json"), "w"))
