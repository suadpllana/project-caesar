#!/usr/bin/env python3
"""How often does a reading of the rule disagree with the sealed model, over drawn task sets?

A reading that moves only a handful of graded sets is a lottery ticket rather than a test of
expertise; CLAUDE.md puts the floor at roughly a tenth. This drives the real engine with a
given policy file over drawn sets and reports the fraction the model disagrees with.

Usage:
    python3 authoring/separation.py <sets> <policy-dir-or-name> [<policy-dir-or-name> ...]
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


def resolve(name):
    for cand in (Path(name), TASK / name, TASK / "authoring" / "variants" / name,
                 TASK / "authoring" / "cheatsrc" / name):
        if (cand / "prio.py").is_file():
            return cand / "prio.py"
    if name == "shipped":
        return TASK / "environment" / "app_src" / "rt" / "prio.py"
    raise SystemExit("no prio.py for %r" % name)


def drive(policy, sets, tmp):
    app = Path(tmp) / "app"
    shutil.copytree(TASK / "environment" / "app_src", app,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    shutil.copyfile(policy, app / "rt" / "prio.py")
    spath = Path(tmp) / "sets.json"
    spath.write_text(json.dumps(sets))
    out = Path(tmp) / "out.json"
    env = dict(os.environ, APP=str(app), SETS=str(spath), OUT=str(out),
               PYTHONDONTWRITEBYTECODE="1")
    proc = subprocess.run([sys.executable, "-c", CHILD], env=env, capture_output=True,
                          text=True, timeout=1800)
    if not out.is_file():
        raise SystemExit("child produced nothing:\n%s\n%s" % (proc.stdout[-2000:],
                                                             proc.stderr[-2000:]))
    return json.loads(out.read_text())


def main(argv):
    n = int(argv[1]) if len(argv) > 1 else 300
    names = argv[2:] or ["solution"]
    sets = scen.batch(scen.seed_from("separation"), n)
    cfg = json.loads((TASK / "tests" / "sched.json").read_text())
    want = [oracle.expect(dict(cfg, **(sc.get("cfg") or {})), sc) for sc in sets]
    for name in names:
        with tempfile.TemporaryDirectory() as tmp:
            got = drive(resolve(name), sets, tmp)
        bad = err = 0
        for g, w in zip(got, want):
            if "err" in g:
                err += 1
                continue
            if any(g[f] != w[f] for f in FIELDS):
                bad += 1
        print("%-40s %4d of %d drawn sets differ (%.1f%%)%s"
              % (name, bad, n, 100.0 * bad / n, "  [%d raised]" % err if err else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
