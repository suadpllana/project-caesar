#!/usr/bin/env python3
"""Regenerate tests/gt.json, proving every number in it before it is written.

Four things have to hold or nothing is written:

  1. The sealed definition and the reference agree on every read, after every job and at the
     end. oracle.Truth keeps the whole record history and never merges anything, so this is
     the statement that the reference's merge is invisible to a reader.
  2. The reference and the shipped plan agree on the job schedule. The trace is the driver's
     and no plan may move it.
  3. runner.SEALED and oracle.SEALED are the same list. They are duplicated because the
     runner cannot import the root-only oracle, and a drift between them silently disarms
     the fingerprint attestation.
  4. authoring/fuzz.py runs clean. The budget is taken from the reference, which is a claim
     that no correct merge needs more work than the reference does; a reference that is
     wrong on a stream nobody wrote down makes that claim worthless.

Usage:
    python3 authoring/build_gt.py [fuzz-streams]
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

TASK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TASK / "authoring"))
sys.path.insert(0, str(TASK / "tests"))

import harness  # noqa: E402
import oracle  # noqa: E402
import runner  # noqa: E402
import scen  # noqa: E402


def cfg_for(sc: dict) -> dict:
    cfg = json.loads((TASK / "tests" / "store.json").read_text())
    cfg.update(sc.get("cfg") or {})
    return cfg


def main(argv: list[str]) -> int:
    if tuple(runner.SEALED) != tuple(oracle.SEALED):
        print("runner.SEALED and oracle.SEALED have drifted apart")
        return 1

    streams = int(argv[1]) if len(argv) > 1 else 600
    proc = subprocess.run([sys.executable, str(TASK / "authoring" / "fuzz.py"),
                           str(streams)], capture_output=True, text=True)
    print(proc.stdout.strip().splitlines()[-1] if proc.stdout else proc.stderr[-800:])
    if proc.returncode:
        print("fuzz did not run clean, refusing to write a ground truth")
        return 1

    ref = harness.run("solution/ref")
    ship = harness.run("shipped")
    if ref.get("errors"):
        print("the reference raised:", ref["errors"])
        return 1
    if ship.get("errors"):
        print("the shipped tree raised:", ship["errors"])
        return 1

    out = {"scenarios": {}}
    for sc in scen.SCENARIOS:
        name = sc["name"]
        cfg = cfg_for(sc)
        t = oracle.Truth(cfg)
        t.run(sc["ops"])
        view = t.map()
        snaps = [[list(x) for x in m] for m in t.snaps]
        r = ref["reports"][name]
        s = ship["reports"][name]
        if r["view"] != view or r["snaps"] != snaps:
            print("%s: the reference disagrees with the sealed definition" % name)
            return 1
        if r["trace"] != s["trace"] or r["jobs"] != s["jobs"]:
            print("%s: the job schedule is not plan independent" % name)
            return 1
        if t.jobs != r["jobs"]:
            print("%s: the sealed model and the engine disagree on how many jobs ran" % name)
            return 1
        out["scenarios"][name] = {
            "view": view,
            "snaps": snaps,
            "reads": r["reads"],
            "writes": r["writes"],
            "probes": r["probes"],
            "shipped_reads": s["reads"],
            "shipped_writes": s["writes"],
            "shipped_probes": s["probes"],
            "trace": r["trace"],
            "jobs": r["jobs"],
        }

    path = TASK / "tests" / "gt.json"
    path.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", newline="\n")
    print("wrote %s" % path)
    for name, e in out["scenarios"].items():
        print("  %-24s reads %-4d writes %-4d probes %-3d   (shipped %d/%d/%d)"
              % (name, e["reads"], e["writes"], e["probes"],
                 e["shipped_reads"], e["shipped_writes"], e["shipped_probes"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
