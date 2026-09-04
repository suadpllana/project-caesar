#!/usr/bin/env python3
"""Try a candidate task set against the model and a list of readings. Authoring only.

Usage: python3 authoring/probe_case.py <case.json> <reading-dir> [...]
Prints, per reading, whether it disagrees with the sealed model and on which field.
"""
from __future__ import annotations
import json, os, shutil, subprocess, sys, tempfile
from pathlib import Path

TASK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TASK / "tests"))
import oracle  # noqa: E402

FIELDS = ("trace", "prio", "ev", "done", "ids", "ticks")
CHILD = r'''
import json, os, sys
sys.path.insert(0, os.environ["APP"])
sc = json.load(open(os.environ["SETS"]))
base = json.load(open(os.path.join(os.environ["APP"], "conf", "sched.json")))
from rt import boot, prio
cfg = dict(base); cfg.update(sc.get("cfg") or {})
c = boot.build(cfg, sc); c.bind(prio.Prio(c)); c.run(cfg["limit"])
json.dump(c.report(), open(os.environ["OUT"], "w"))
'''

def resolve(name):
    for cand in (Path(name), TASK / name, TASK / "authoring" / "variants" / name,
                 TASK / "authoring" / "cheatsrc" / name):
        if (cand / "prio.py").is_file():
            return cand / "prio.py"
    if name == "shipped":
        return TASK / "environment" / "app_src" / "rt" / "prio.py"
    raise SystemExit("no prio.py for %r" % name)

def drive(policy, sc):
    with tempfile.TemporaryDirectory() as tmp:
        app = Path(tmp) / "app"
        shutil.copytree(TASK / "environment" / "app_src", app,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        shutil.copyfile(policy, app / "rt" / "prio.py")
        sp = Path(tmp) / "sc.json"; sp.write_text(json.dumps(sc))
        out = Path(tmp) / "o.json"
        env = dict(os.environ, APP=str(app), SETS=str(sp), OUT=str(out),
                   PYTHONDONTWRITEBYTECODE="1")
        pr = subprocess.run([sys.executable, "-c", CHILD], env=env, capture_output=True, text=True)
        if not out.is_file():
            return {"err": (pr.stderr or pr.stdout)[-600:]}
        return json.loads(out.read_text())

def check(sc, names):
    cfg = json.loads((TASK / "tests" / "sched.json").read_text())
    want = oracle.expect(dict(cfg, **(sc.get("cfg") or {})), sc)
    rows = []
    for name in names:
        got = drive(resolve(name), sc)
        if "err" in got:
            rows.append((name, "RAISED", got["err"][:120])); continue
        diff = [f for f in FIELDS if got[f] != want[f]]
        rows.append((name, "differs" if diff else "agrees", ",".join(diff)))
    return want, rows

if __name__ == "__main__":
    sc = json.loads(Path(sys.argv[1]).read_text())
    want, rows = check(sc, sys.argv[2:])
    print("model ticks=%s done=%s" % (want["ticks"], want["done"]))
    for n, v, d in rows:
        print("  %-46s %-8s %s" % (n, v, d))
