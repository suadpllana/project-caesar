#!/usr/bin/env python3
"""Per cheat, which graded field diverges from ground truth.

A field that separates no cheat is pure liability: it cannot catch a wrong answer and it
can still fail a right one. A field that separates only cheats some other field already
catches is redundant but harmless. This prints the matrix so the graded set can be judged
rather than assumed.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

TASK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TASK / "authoring"))

sys.path.insert(0, str(TASK / "tests"))

import harness  # noqa: E402
import oracle  # noqa: E402
import scen  # noqa: E402

BODY = re.compile(r"<<'EOF_ROUTE'\n(.*?)\nEOF_ROUTE", re.S)
# The last three are the evidence axis. They have no ground truth of their own: they hold
# when the work journal accounts for the counters, reproduces the values the submission
# published, and contains only records the scenario made possible.
FIELDS = ("view", "log", "folds", "scans", "trace", "emits", "revised",
          "journal", "replay", "audit")


def evidence(got: dict, cfg: dict, ops: list) -> set:
    out = set()
    jrn = got.get("jrn")
    if oracle.shape(jrn) is not None:
        return {"journal", "replay", "audit"}
    if (sum(1 for e in jrn if e[0] == "f") != got.get("folds")
            or sum(1 for e in jrn if e[0] == "s") != got.get("scans")
            or sum(1 for e in jrn if e[0] == "e") != got.get("emits")):
        out.add("journal")
    view, emitted, why = oracle.replay(jrn)
    if why or view != got.get("view") or emitted != [list(x) for x in (got.get("log") or [])]:
        out.add("replay")
    if oracle.audit(jrn, ops, cfg) is not None:
        out.add("audit")
    return out


def run_src(src: str) -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        app = tmp / "app"
        harness.overlay("shipped", app)
        (app / "view" / "route.py").write_text(src)
        out = tmp / "out.json"
        subprocess.run(
            [sys.executable, str(TASK / "tests" / "runner.py"), str(out)],
            capture_output=True, text=True, timeout=900,
            env={"APPDIR": str(app), "PYTHONDONTWRITEBYTECODE": "1",
                 "SYSTEMROOT": "C:\\Windows", "PATH": "/usr/bin:/bin"})
        if not out.is_file():
            return {"reports": {}}
        return json.loads(out.read_text())


def diverging(rep: dict, gt: dict) -> set:
    base = json.loads((TASK / "tests" / "view.json").read_text())
    out = set()
    for name, exp in gt["scenarios"].items():
        got = (rep.get("reports") or {}).get(name)
        if not isinstance(got, dict):
            out.update(FIELDS)
            continue
        sc = scen.by_name(name)
        cfg = dict(base)
        for k, v in (sc.get("cfg") or {}).items():
            cfg[k] = v
        out |= evidence(got, cfg, sc["ops"])
        for f in FIELDS[:7]:
            a, b = got.get(f), exp.get(f)
            if f in ("log", "trace"):
                a = [list(x) for x in a] if isinstance(a, list) else a
                b = [list(x) for x in b]
            if a != b:
                out.add(f)
    return out


def main() -> int:
    gt = json.loads((TASK / "tests" / "gt.json").read_text())
    rows = []
    for sh in sorted((TASK / "cheat").glob("cheat-*.sh")):
        m = BODY.search(sh.read_text())
        if not m:
            continue
        rows.append((sh.name.replace("cheat-", "").replace(".sh", ""),
                     diverging(run_src(m.group(1)), gt)))
    w = max(len(n) for n, _ in rows)
    print("%-*s  %s" % (w, "cheat", "  ".join("%-7s" % f for f in FIELDS)))
    for name, div in rows:
        print("%-*s  %s" % (w, name,
                            "  ".join("%-7s" % ("X" if f in div else ".") for f in FIELDS)))
    print()
    dead = [f for f in FIELDS if not any(f in d for _, d in rows)]
    if dead:
        print("DEAD WEIGHT (separates no cheat): %s" % ", ".join(dead))
        return 1
    print("every graded field separates at least one cheat")
    return 0


if __name__ == "__main__":
    sys.exit(main())
