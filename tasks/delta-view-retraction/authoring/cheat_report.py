#!/usr/bin/env python3
"""Run every cheat through the real verifier and report which test catches it.

Each cheat/*.sh writes one file, /app/view/route.py, as a heredoc. This extracts that
body, overlays it the way test.sh does, runs the real runner and the real grader, and
records the reward plus the first assertion that fired.

Every cheat must score 0. A cheat that scores 1 means the verifier has a hole.
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


def body_of(sh: Path) -> str | None:
    m = BODY.search(sh.read_text())
    return m.group(1) if m else None


def grade(route_src: str) -> tuple[int, str]:
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        app = tmp / "app"
        harness.overlay("shipped", app)
        (app / "view" / "route.py").write_text(route_src)
        # What the harness would have uploaded, which is what the attestation compares
        # the executed tree against.
        art = tmp / "artifact" / "view"
        art.mkdir(parents=True)
        (art / "route.py").write_text(route_src)
        out = tmp / "out.json"
        subprocess.run(
            [sys.executable, str(TASK / "tests" / "runner.py"), str(out)],
            capture_output=True, text=True, timeout=900,
            env={"APPDIR": str(app), "PYTHONDONTWRITEBYTECODE": "1",
                 "RUN_NONCE": "hostemulation", "TMPDIR": str(tmp),
                 "SYSTEMROOT": "C:\\Windows", "PATH": "/usr/bin:/bin"})
        if not out.is_file():
            out.write_text(json.dumps({"reports": {}, "errors": {"fatal": "no output"}}))
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "--tb=no",
             str(TASK / "tests" / "test_outputs.py")],
            capture_output=True, text=True, timeout=900,
            env={"RUN_OUT": str(out),
                 "RUN_NONCE": "hostemulation",
                 "APP_DIR": str(app),
                 "PRISTINE_DIR": str(TASK / "environment" / "app_src"),
                 "ARTIFACT_DIR": str(tmp / "artifact"),
                 "PYTHONPATH": str(TASK / "tests"), "PYTHONDONTWRITEBYTECODE": "1",
                 "SYSTEMROOT": "C:\\Windows", "PATH": "/usr/bin:/bin"})
        first = ""
        for line in proc.stdout.splitlines():
            if line.startswith("FAILED"):
                first = line.split("::")[-1].split(" ")[0]
                break
        return (1 if proc.returncode == 0 else 0), first


def main() -> int:
    bad = 0
    rows = []
    for sh in sorted((TASK / "cheat").glob("cheat-*.sh")):
        src = body_of(sh)
        if src is None:
            rows.append((sh.name, "-", "no route body found"))
            continue
        r, first = grade(src)
        if r != 0:
            bad += 1
        rows.append((sh.name, r, first or "(none)"))
    w = max(len(n) for n, _, _ in rows)
    for name, r, first in rows:
        flag = "OK " if r == 0 else "BAD"
        print("%s %-*s reward=%s  first failure: %s" % (flag, w, name, r, first))
    print("\n%d cheats, %d scored non-zero" % (len(rows), bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
