#!/usr/bin/env python3
"""Report which assertions each cheat trips, so cheat/README stays honest.

Usage:  python3 authoring/cheat_report.py
"""

from __future__ import annotations

import collections
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

TASK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TASK / "authoring"))

import harness  # noqa: E402

EDITABLE = ["tok/inc.py", "tok/store.py", "loop/ep.py", "loop/rec.py"]


def trial(script: Path | None):
    app_live = Path("/app")
    if app_live.exists():
        shutil.rmtree(app_live)
    shutil.copytree(TASK / "environment" / "app_src", app_live)
    if script is not None:
        subprocess.run(["bash", str(script)], capture_output=True)
    with tempfile.TemporaryDirectory() as tmp:
        app = Path(tmp) / "app"
        shutil.copytree(TASK / "tests" / "pristine", app)
        for rel in EDITABLE:
            if (app_live / rel).is_file():
                shutil.copyfile(app_live / rel, app / rel)
        out = Path(tmp) / "out.json"
        tape = Path(tmp) / "tape.jsonl"
        env = dict(os.environ)
        env.update({"APPDIR": str(app), "PYTHONDONTWRITEBYTECODE": "1"})
        # The meter runs for the trial the way test.sh runs it for the real thing. A
        # trial without one would grade the run's own account of itself.
        served = harness.meter(tape)
        try:
            subprocess.run([sys.executable, str(TASK / "tests" / "runner.py"), str(out)],
                           capture_output=True, env=env)
        finally:
            if served is not None:
                served.terminate()
                served.wait(timeout=10)
        env["RUN_OUT"] = str(out)
        env["RUN_TAPE"] = str(tape)
        env["PYTHONPATH"] = str(TASK / "tests")
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "--tb=no",
             str(TASK / "tests" / "test_outputs.py")],
            capture_output=True, text=True, env=env)
    fails = collections.defaultdict(list)
    for line in proc.stdout.splitlines():
        if line.startswith("FAILED"):
            body = line.split("::", 1)[1]
            test = body.split("[")[0]
            case = body.split("[")[1].rstrip("]") if "[" in body else ""
            fails[test].append(case)
    return proc.returncode, fails


def main() -> int:
    rc, fails = trial(TASK / "solution" / "solve.sh")
    print("oracle: rc=%d %s" % (rc, dict(fails) or "clean"))
    rc, fails = trial(None)
    print("nop:    rc=%d trips %s\n" % (rc, ", ".join(sorted(fails))))
    for cheat in sorted((TASK / "cheat").glob("*.sh")):
        rc, fails = trial(cheat)
        print(cheat.name)
        for test in sorted(fails):
            print("    %-40s %s" % (test, " ".join(sorted(fails[test]))))
        if rc == 0:
            print("    SCORED 1 - verifier bug")
    return 0


if __name__ == "__main__":
    sys.exit(main())
