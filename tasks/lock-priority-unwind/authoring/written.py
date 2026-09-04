#!/usr/bin/env python3
"""Which written scenarios separate each reading? Authoring only.

The drawn half is the anti-memorisation half. The written half is what has to catch a wrong
reading with certainty, so that a misreading surfaces as a named case rather than as "a few of
three hundred random sets wrong". A reading that no written scenario separates is a lottery
ticket whatever its drawn percentage.

Usage: python3 authoring/written.py <reading> [<reading> ...]
"""
from __future__ import annotations
import json, sys
from pathlib import Path

TASK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TASK / "tests"))
sys.path.insert(0, str(TASK / "authoring"))
import oracle, scen, probe_case  # noqa: E402

FIELDS = ("trace", "prio", "ev", "done", "ids", "ticks")

def main(argv):
    cfg = json.loads((TASK / "tests" / "sched.json").read_text())
    want = {sc["name"]: oracle.expect(dict(cfg, **(sc.get("cfg") or {})), sc)
            for sc in scen.SCENARIOS}
    worst = 0
    for name in argv[1:]:
        pol = probe_case.resolve(name)
        hits, raised = [], 0
        for sc in scen.SCENARIOS:
            got = probe_case.drive(pol, sc)
            if "err" in got:
                raised += 1
                continue
            if any(got[f] != want[sc["name"]][f] for f in FIELDS):
                hits.append(sc["name"])
        flag = "" if hits else "   <-- SEPARATED BY NOTHING"
        print("%-38s %2d of %d written%s%s"
              % (name, len(hits), len(scen.SCENARIOS),
                 "  [%d raised]" % raised if raised else "", flag))
        if hits:
            print("      " + ", ".join(hits[:6]) + (" ..." if len(hits) > 6 else ""))
        if not hits:
            worst = 1
    return worst

if __name__ == "__main__":
    sys.exit(main(sys.argv))
