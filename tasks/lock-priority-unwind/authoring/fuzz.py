#!/usr/bin/env python3
"""The reference against the sealed model on drawn task sets.

The verifier grades scenarios that do not exist until it runs them, so the reference has to be
right in general and not only about the fourteen shapes somebody thought to write down. This
draws task sets the same way the verifier does and requires the engine, driven by the reference
policy, to reproduce the model's schedule, priority table, lifecycle log and finish times
exactly.

Usage:
    python3 authoring/fuzz.py [sets] [seed]
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

TASK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TASK / "tests"))

import oracle  # noqa: E402
import scen  # noqa: E402

FIELDS = ("trace", "prio", "ev", "done", "ids", "ticks")

CHILD = r'''
import json, os, sys
sys.path.insert(0, os.environ["APP"])
sets = json.load(open(os.environ["SETS"]))
base = json.load(open(os.path.join(os.environ["APP"], "conf", "sched.json")))
out = []
for sc in sets:
    for m in list(sys.modules):
        if m.split(".")[0] == "rt":
            sys.modules.pop(m, None)
    from rt import boot, prio
    cfg = dict(base); cfg.update(sc.get("cfg") or {})
    try:
        c = boot.build(cfg, sc)
        c.bind(prio.Prio(c))
        c.run(cfg["limit"])
        out.append(c.report())
    except Exception as e:
        out.append({"err": repr(e)})
json.dump(out, open(os.environ["OUT"], "w"))
'''


def main(argv: list[str]) -> int:
    n = int(argv[1]) if len(argv) > 1 else 400
    seed = argv[2] if len(argv) > 2 else "fuzz-2026-08-15"
    sets = scen.batch(scen.seed_from(seed), n)
    cfg = json.loads((TASK / "tests" / "sched.json").read_text())

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        app = tmp / "app"
        shutil.copytree(TASK / "environment" / "app_src", app,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        shutil.copyfile(TASK / "solution" / "prio.py", app / "rt" / "prio.py")
        sp = tmp / "sets.json"
        sp.write_text(json.dumps(sets))
        out = tmp / "out.json"
        env = dict(os.environ)
        env.update({"APP": str(app), "SETS": str(sp), "OUT": str(out),
                    "PYTHONDONTWRITEBYTECODE": "1"})
        proc = subprocess.run([sys.executable, "-c", CHILD], capture_output=True,
                              text=True, env=env)
        if not out.is_file():
            print(proc.stdout[-2000:], proc.stderr[-2000:])
            return 1
        got = json.loads(out.read_text())

    bad = 0
    ticks = 0
    for sc, g in zip(sets, got):
        want = oracle.expect(cfg, sc)
        if "err" in g:
            bad += 1
            print("RAISED", g["err"])
            print(json.dumps(sc))
            continue
        ticks += want["ticks"]
        for f in FIELDS:
            if g[f] != want[f]:
                bad += 1
                print("MISMATCH on %s in %s" % (f, sc["name"]))
                print(json.dumps(sc))
                for i, (a, b) in enumerate(zip(g[f], want[f]) if isinstance(want[f], list)
                                           else []):
                    if a != b:
                        print("  at %d: engine %r model %r" % (i, a, b))
                        break
                break
        if bad > 3:
            break

    print("%d drawn sets, %d ticks simulated, %d mismatches" % (len(sets), ticks, bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
