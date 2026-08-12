#!/usr/bin/env python3
"""Does the graded corpus still put every scenario in the position its aim describes?

The service generates the corpus from a seed the trainer never sees, and that seed is not
the one in the tree the agent works in, so the sample lengths under grading are not the
lengths the agent's own runs produce.  That is what stops a submission from computing the
answer instead of asking for it.  It also means the scenario set has to be re-checked
against the graded corpus: a save is only a save with an item held if the packing under
*that* corpus leaves an item held there, and a scenario whose aim no longer holds is a
scenario that has stopped separating the mistake it was built to separate.

Every property below is checked against tests/corpus.json, and build_gt.py refuses to
write a ground truth when any of them fails.

Usage:
    python3 authoring/corpus_check.py
    python3 authoring/corpus_check.py --search 40
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

TASK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TASK / "tests"))
sys.path.insert(0, str(TASK / "authoring"))

import oracle  # noqa: E402
import scen  # noqa: E402


def cfg_for(sc):
    cfg = json.loads((TASK / "environment" / "app_src" / "conf" / "train.json").read_text())
    for k, v in (sc.get("over") or {}).items():
        if k == "sched":
            for a, b in v.items():
                cfg["sched"][a] = b
        else:
            cfg[k] = v
    return cfg


def probe(sc, ds):
    """Replay one scenario op by op, recording the state at every save and load."""
    r = oracle.Run(cfg_for(sc), ds)
    out = {"saves": [], "loads": [], "rolled": [], "rows": []}
    at_save = None
    for op in sc["ops"]:
        o = op.get("op")
        if o == "save":
            st = r.st
            at_save = r.ctr["reads"]
            out["saves"].append({
                "step": st["step"], "k": st["k"], "ws": st["ws"], "cur": st["cur"],
                "hold": None if st["hold"] is None else list(st["hold"]),
                "sched": list(oracle.sched(r.cfg, st["step"])),
            })
        r.apply([op])
        if o == "load":
            st = r.st
            out["loads"].append({
                "step": st["step"], "k": st["k"], "cur": st["cur"],
                "hold": None if st["hold"] is None else list(st["hold"]),
                "sched": list(oracle.sched(r.cfg, st["step"])),
            })
            if at_save is not None:
                out["rolled"].append(r.ctr["reads"] - at_save)
    out["rows"] = [int(e.split(":")[2]) for e in r.tr if e.startswith("m:")]
    out["end"] = {"step": r.st["step"], "cur": r.st["cur"], "reads": r.ctr["reads"]}
    out["nsamp"] = r.cfg["nsamp"]
    return out


def held(pr, which=0):
    return pr["saves"][which]["hold"] is not None


def open_window(pr, which=0):
    return pr["saves"][which]["k"] > 0


CHECKS = {
    "straight": [
        ("runs to several updates", lambda p: p["end"]["step"] >= 6),
        ("the row count varies between microbatches", lambda p: len(set(p["rows"])) > 1),
    ],
    "empty-carry": [
        ("nothing is held and the cursor is at zero",
         lambda p: not held(p) and p["saves"][0]["cur"] == 0),
    ],
    "boundary": [
        ("the save sits on a window boundary", lambda p: not open_window(p)),
        ("an item is held across it", held),
    ],
    "midwindow": [
        ("a window is open at the save", open_window),
        ("an item is held across it", held),
        ("the open window has taken tokens in", lambda p: p["saves"][0]["step"] >= 1),
    ],
    "carry-bump": [
        ("an item is held across the save", held),
        ("the held bound is not the bound in force where it is placed",
         lambda p: p["saves"][0]["hold"][1] != p["saves"][0]["sched"][1]),
    ],
    "rollback": [
        ("the load rolls real reads back", lambda p: p["rolled"][0] > 20),
    ],
    "epoch": [
        ("the cursor crosses an epoch boundary after the load",
         lambda p: p["end"]["cur"] // p["nsamp"] > p["loads"][0]["cur"] // p["nsamp"]),
    ],
    "amend-lr": [
        ("a window is open at the save", open_window),
    ],
    "amend-bound": [
        ("an item is held across the save", held),
        ("the amended bound is not the bound the held item was drawn under",
         lambda p: p["saves"][0]["hold"][1] != p["loads"][0]["sched"][1]),
    ],
    "amend-window": [
        ("a window is open at the save", open_window),
        ("the amendment shortens the window that was already open",
         lambda p: p["saves"][0]["ws"] > p["loads"][0]["sched"][2]),
        ("the open window still has a microbatch to run under its latched length",
         lambda p: p["saves"][0]["k"] < p["saves"][0]["ws"]),
    ],
    "amend-ema": [
        ("a window is open at the save", open_window),
        ("the amended shift differs from the one in force at the save",
         lambda p: p["saves"][0]["sched"][3] != p["loads"][0]["sched"][3]),
    ],
    "twice": [
        ("two cycles", lambda p: len(p["loads"]) == 2),
        ("something is held across one of them",
         lambda p: any(s["hold"] is not None for s in p["saves"])),
    ],
    "wide": [
        ("the wider bin still packs every microbatch", lambda p: min(p["rows"]) > 0),
        ("the lifecycle completes under the other packing shape",
         lambda p: p["end"]["step"] >= 6 and len(p["loads"]) == 1),
    ],
    "long": [
        ("three cycles", lambda p: len(p["loads"]) == 3),
        ("a window is open at one of the saves",
         lambda p: any(s["k"] > 0 for s in p["saves"])),
        ("something is held across one of them",
         lambda p: any(s["hold"] is not None for s in p["saves"])),
    ],
}


def check(ds, quiet=False):
    bad = 0
    for sc in scen.SCENARIOS:
        try:
            pr = probe(sc, ds)
        except Exception as exc:
            print("RAISED %-13s %s" % (sc["name"], exc))
            bad += 1
            continue
        for label, fn in CHECKS.get(sc["name"], []):
            try:
                ok = bool(fn(pr))
            except Exception:
                ok = False
            if not ok:
                bad += 1
                if not quiet:
                    print("FAIL %-13s %s" % (sc["name"], label))
            elif not quiet:
                print("ok   %-13s %s" % (sc["name"], label))
    return bad


def main(argv):
    if "--search" in argv:
        n = int(argv[argv.index("--search") + 1])
        seen = 0
        for ds in range(10007, 10007 + 200000, 7):
            if check(ds, quiet=True) == 0:
                print("clean corpus seed: %d" % ds)
                seen += 1
                if seen >= n:
                    break
        return 0
    ds = json.loads((TASK / "tests" / "corpus.json").read_text())["dseed"]
    tree = json.loads(
        (TASK / "environment" / "app_src" / "conf" / "corpus.json").read_text())["dseed"]
    cfg = json.loads((TASK / "environment" / "app_src" / "conf" / "train.json").read_text())
    bad = check(ds)
    if ds == tree:
        print("FAIL the graded corpus is the one shipped in the tree")
        bad += 1
    if ds == cfg["seed"]:
        print("FAIL the graded corpus seed is the trainer seed")
        bad += 1
    print("\ncorpus %d: %s" % (ds, "every scenario keeps its aim" if not bad
                               else "%d property/properties lost" % bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
