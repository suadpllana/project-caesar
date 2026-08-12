#!/usr/bin/env python3
"""Regenerate tests/gt.json, and refuse to write a ground truth it cannot prove.

Three things have to line up before anything is written:

  1. The reference solution's report for every scenario.
  2. The sealed generator in tests/oracle.py, which shares no code with the tree and
     implements the lifecycle from scratch, on the same op list.
  3. The same generator on the compacted op list - the down time deleted, the amendments
     that landed in it kept - which never checkpoints at all and is the task's definition
     of what a correct resume has to agree with from the load onward.

(1) must equal (2) on every graded field, and (2) must equal (3) on the parameters, the
shadow average and the step counter.  If either fails, this refuses to write.

Usage:  python3 authoring/build_gt.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

TASK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TASK / "tests"))
sys.path.insert(0, str(TASK / "authoring"))

import harness  # noqa: E402
import oracle  # noqa: E402
import scen  # noqa: E402

GRADED = ("p", "ema", "step", "reads", "pos", "upd", "trace")


def cfg_for(sc):
    cfg = json.loads((TASK / "environment" / "app_src" / "conf" / "train.json").read_text())
    for k, v in (sc.get("over") or {}).items():
        if k == "sched":
            for a, b in v.items():
                cfg["sched"][a] = b
        else:
            cfg[k] = v
    return cfg


def main() -> int:
    ref = harness.run("solution/ref")
    if ref.get("errors"):
        print("reference raised:", ", ".join(sorted(ref["errors"])))
        return 1

    out = {"scenarios": {}}
    bad = 0
    for sc in scen.SCENARIOS:
        name = sc["name"]
        cfg = cfg_for(sc)
        want = oracle.run(cfg, sc["ops"])
        got = ref["reports"].get(name)
        for f in GRADED:
            if got is None or got[f] != want[f]:
                print("MISMATCH %-13s %-6s reference=%r oracle=%r"
                      % (name, f, None if got is None else got[f], want[f]))
                bad += 1
        comp = oracle.run(cfg, oracle.compact(sc["ops"]))
        for f in ("p", "ema", "step"):
            if comp[f] != want[f]:
                print("NOT EQUIVALENT %-13s %-4s compacted=%r lifecycle=%r"
                      % (name, f, comp[f], want[f]))
                bad += 1
        out["scenarios"][name] = {"report": {f: want[f] for f in GRADED}}

    if bad:
        print("\n%d disagreement(s) - ground truth not written" % bad)
        return 1

    dest = TASK / "tests" / "gt.json"
    dest.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    dest.chmod(0o600)
    print("wrote %s for %d scenarios, all three sources agreeing"
          % (dest.relative_to(TASK), len(out["scenarios"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
