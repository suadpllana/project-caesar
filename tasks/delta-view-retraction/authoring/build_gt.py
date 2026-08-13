#!/usr/bin/env python3
"""Regenerate tests/gt.json, refusing to write a ground truth it cannot prove.

Ground truth is produced by running the REFERENCE solution, but it is only written after
the sealed oracle in tests/oracle.py - which shares no code with the engine tree and
folds every aggregate over the full surviving multiset with no cap and no cache - agrees
with it on every emitted value and on the final view of every scenario.

That agreement is the load-bearing claim of the whole task: the engine's bounded
accumulator is an optimisation, and the reference is only correct because it falls back to
the row store exactly when the accumulator stops being a faithful witness. If the two ever
disagree, the reference is wrong and no ground truth is written.

It also proves the premise the instruction rests on: the SHIPPED engine already produces
these same values, and differs only in how much work it does. A ground truth whose values
the shipped tree does not already reproduce would mean the task is about correctness
rather than about work, which is not the task that was designed.
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


def cfg_for(sc, base):
    cfg = json.loads(json.dumps(base))
    for k, v in (sc.get("cfg") or {}).items():
        cfg[k] = v
    return cfg


def main() -> int:
    base = json.loads((TASK / "environment" / "app_src" / "conf" / "view.json").read_text())

    ref = harness.run("solution/ref")
    if ref.get("errors"):
        print("reference raised:", ref["errors"])
        return 1
    shipped = harness.run("shipped")
    if shipped.get("errors"):
        print("shipped tree raised:", shipped["errors"])
        return 1

    out = {"scenarios": {}}
    bad = []
    for sc in scen.SCENARIOS:
        name = sc["name"]
        rep = ref["reports"].get(name)
        shp = shipped["reports"].get(name)
        if rep is None or shp is None:
            bad.append("%s: missing report" % name)
            continue

        t = oracle.Truth(cfg_for(sc, base))
        t.run(sc["ops"])

        # 1. The reference's final view must equal the sealed definition.
        if rep["view"] != t.view():
            bad.append("%s: reference view %s != oracle %s" % (name, rep["view"], t.view()))
        # 2. Every value the reference emitted must equal the sealed definition.
        if [list(x) for x in rep["log"]] != [list(x) for x in t.log]:
            bad.append("%s: reference emit log disagrees with the oracle" % name)
        # 3. The shipped tree must already agree on values: the bug is work, not values.
        if shp["view"] != t.view():
            bad.append("%s: shipped view %s != oracle %s" % (name, shp["view"], t.view()))
        if [list(x) for x in shp["log"]] != [list(x) for x in t.log]:
            bad.append("%s: shipped emit log disagrees with the oracle" % name)
        # 4. The reference must actually be cheaper, or there is no task.
        if not (rep["folds"] < shp["folds"] and rep["scans"] < shp["scans"]):
            bad.append("%s: reference is not cheaper than the shipped tree "
                       "(folds %d vs %d, scans %d vs %d)"
                       % (name, rep["folds"], shp["folds"], rep["scans"], shp["scans"]))

        out["scenarios"][name] = {
            "view": rep["view"],
            "folds": rep["folds"],
            "scans": rep["scans"],
            "emits": rep["emits"],
            "revised": rep["revised"],
            "log": [list(x) for x in rep["log"]],
            "trace": [list(x) for x in rep["trace"]],
            "shipped_folds": shp["folds"],
            "shipped_scans": shp["scans"],
        }

    if bad:
        print("REFUSING to write ground truth:")
        for b in bad:
            print("  -", b)
        return 1

    (TASK / "tests" / "gt.json").write_text(
        json.dumps(out, indent=1, sort_keys=True), encoding="utf-8", newline="\n"
    )
    print("wrote gt.json for %d scenarios" % len(out["scenarios"]))
    for name, s in sorted(out["scenarios"].items()):
        print("  %-22s folds %4d (shipped %4d)  scans %3d (shipped %3d)"
              % (name, s["folds"], s["shipped_folds"], s["scans"], s["shipped_scans"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
