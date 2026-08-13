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

import harness  # noqa: E402

BODY = re.compile(r"<<'EOF_ROUTE'\n(.*?)\nEOF_ROUTE", re.S)
FIELDS = ("view", "log", "folds", "scans", "trace", "emits", "revised")


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
    out = set()
    for name, exp in gt["scenarios"].items():
        got = (rep.get("reports") or {}).get(name)
        if not isinstance(got, dict):
            out.update(FIELDS)
            continue
        for f in FIELDS:
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
