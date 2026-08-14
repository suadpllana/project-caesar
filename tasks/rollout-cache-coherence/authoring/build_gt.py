#!/usr/bin/env python3
"""Generate tests/gt.json from the reference solution, and prove every expected token
stream against the sealed oracle before writing it.

For each scenario the reference engine is run over the scenario op list; then, for each
request, the sealed generator in tests/oracle.py is asked to produce that request's
tokens from scratch under every parameter snapshot the scenario passes through.  The
reported stream must equal at least one of them - that is the proof that the engine's
answer is a real single-policy sample and not an artefact of cache reuse.  The matching
snapshot indices are recorded so the verifier can repeat the proof without the engine.

Usage:  python3 authoring/build_gt.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

TASK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TASK / "authoring"))
sys.path.insert(0, str(TASK / "tests"))

import harness  # noqa: E402
import oracle  # noqa: E402
import scen  # noqa: E402


def requests(ops):
    out = []
    for op in ops:
        if op["op"] == "add":
            out.append((op["rid"], op["prompt"], op.get("adapter"), op["max_new"]))
    return out


def main() -> int:
    cfg = json.loads((TASK / "environment" / "app_src" / "conf" / "engine.json").read_text())
    data = harness.run("solution/ref")
    if data.get("errors"):
        for name, err in data["errors"].items():
            print("reference failed on", name, "\n", err)
        return 1

    gt = {"scenarios": {}}
    for sc in scen.SCENARIOS:
        name = sc["name"]
        rep = data["reports"][name]
        snaps = oracle.snapshots(cfg["seeds"], cfg["adapters"], sc["ops"])
        matches = {}
        for rid, prompt, adapter, max_new in requests(sc["ops"]):
            if rid not in rep["out"]:
                print("scenario", name, "left", rid, "unfinished")
                return 1
            got = rep["out"][rid]
            hits = []
            for i, (seeds, ad) in enumerate(snaps):
                deltas = ad.get(adapter, {}) if adapter else {}
                if oracle.generate(seeds, deltas, rid, prompt, max_new) == got:
                    hits.append(i)
            if not hits:
                print("scenario", name, "request", rid,
                      "produced a stream matching no parameter snapshot")
                return 1
            matches[rid] = hits
        gt["scenarios"][name] = {"report": rep, "snap": matches}
        print("%-22s ok  requests=%-3d snapshots=%d" % (name, len(matches), len(snaps)))

    (TASK / "tests" / "gt.json").write_text(
        json.dumps(gt, indent=1, sort_keys=True) + "\n", newline="\n")
    print("\nwrote tests/gt.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
