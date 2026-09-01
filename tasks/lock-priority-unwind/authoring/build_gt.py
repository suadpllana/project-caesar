#!/usr/bin/env python3
"""Regenerate tests/gt.json, proving every schedule in it before it is written.

Four things have to hold or nothing is written:

  1. The sealed model and the reference agree on every graded field of every written scenario.
     The model never patches a priority; it solves the whole assignment as a fixed point. The
     reference patches incrementally. Agreement between the two is the statement that the
     incremental policy is a correct optimisation of the definition.
  2. The reference and the shipped policy agree on the task set and the settings, so a
     difference between them is a difference of policy and not of setup.
  3. runner.SEALED and oracle.SEALED are the same list. They are duplicated because the runner
     cannot import the root-only model, and a drift between them silently disarms the
     fingerprint attestation.
  4. authoring/fuzz.py runs clean on drawn task sets. The verifier grades scenarios that do not
     exist until it runs them, so a reference that is right about the fourteen written shapes
     and wrong in general would fail its own task.

Usage:
    python3 authoring/build_gt.py [drawn-sets]
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

FIELDS = ("trace", "prio", "ev", "done", "ids", "ticks")


def settings(sc):
    c = json.loads((TASK / "tests" / "sched.json").read_text())
    c.update(sc.get("cfg") or {})
    return c


def main(argv: list[str]) -> int:
    if tuple(runner.SEALED) != tuple(oracle.SEALED):
        print("runner.SEALED and oracle.SEALED have drifted apart")
        return 1

    n = argv[1] if len(argv) > 1 else "400"
    proc = subprocess.run([sys.executable, str(TASK / "authoring" / "fuzz.py"), n],
                          capture_output=True, text=True)
    tail = proc.stdout.strip().splitlines()
    print(tail[-1] if tail else proc.stderr[-800:])
    if proc.returncode:
        print("the reference disagrees with the model on drawn task sets, refusing to write")
        return 1

    ref = harness.run("solution/ref")
    ship = harness.run("shipped")
    if ref.get("broke"):
        print("the reference raised:", ref["broke"])
        return 1

    out = {"scenarios": {}}
    split = 0
    for sc in scen.SCENARIOS:
        name = sc["name"]
        want = oracle.expect(settings(sc), sc)
        mine = ref["runs"][name]
        for f in FIELDS:
            if mine[f] != want[f]:
                print("%s: the reference disagrees with the sealed model on %s" % (name, f))
                return 1
        theirs = ship["runs"].get(name, {})
        if theirs.get("trace") != want["trace"] or theirs.get("prio") != want["prio"]:
            split += 1
        out["scenarios"][name] = dict((f, want[f]) for f in FIELDS)

    path = TASK / "tests" / "gt.json"
    path.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", newline="\n")
    print("wrote %s" % path)
    print("the shipped policy differs from the reference on %d of the %d written scenarios"
          % (split, len(scen.SCENARIOS)))
    for name, e in out["scenarios"].items():
        print("  %-28s ticks %-4d tasks %d" % (name, e["ticks"], len(e["ids"])))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
