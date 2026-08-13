#!/usr/bin/env python3
"""Run alternative correct implementations through the real verifier.

The cheat suite proves wrong answers score 0. This proves the other direction, which the
run audit is what actually checks: that a solution which got the semantics right does not
lose on an implementation choice the instruction never asked for. Every variant in
authoring/variants/ok-* must score 1.

A variant directory holds only the files it changes. Everything else is taken from
solution/ref, so the suite cannot quietly rot into testing the shipped tree when the
reference moves.

Usage:  python3 authoring/variant_check.py
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
EDITABLE = {
    "pstore.py": "model/pstore.py",
    "pfx.py": "runtime/pfx.py",
    "sch.py": "runtime/sch.py",
    "pool.py": "mem/pool.py",
}


def score(variant: Path) -> tuple[int, str]:
    with tempfile.TemporaryDirectory() as tmp:
        app = Path(tmp) / "app"
        shutil.copytree(TASK / "tests" / "pristine", app)
        for name, rel in EDITABLE.items():
            src = variant / name
            if not src.is_file():
                src = TASK / "solution" / "ref" / name
            shutil.copyfile(src, app / rel)
        out = Path(tmp) / "out.json"
        env = dict(os.environ)
        env.update({"APPDIR": str(app), "PYTHONDONTWRITEBYTECODE": "1"})
        subprocess.run([sys.executable, str(TASK / "tests" / "runner.py"), str(out)],
                       capture_output=True, env=env, timeout=900)
        env["RUN_OUT"] = str(out)
        env["CONF_JSON"] = str(TASK / "tests" / "engine.json")
        env["PYTHONPATH"] = str(TASK / "tests")
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "--tb=no",
             str(TASK / "tests" / "test_outputs.py")],
            capture_output=True, text=True, env=env)
    fails = sorted({ln.split("::", 1)[1].split("[")[0] for ln in proc.stdout.splitlines()
                    if ln.startswith("FAILED")})
    return (1 if proc.returncode == 0 else 0), ", ".join(fails)


def main() -> int:
    root = TASK / "authoring" / "variants"
    bad = 0
    for variant in sorted(p for p in root.iterdir() if p.is_dir()):
        want = 1 if variant.name.startswith("ok-") else 0
        got, fails = score(variant)
        mark = "PASS" if got == want else "FAIL"
        print("%-22s reward=%d expected=%d %s %s" % (variant.name, got, want, mark, fails))
        if got != want:
            bad += 1
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
