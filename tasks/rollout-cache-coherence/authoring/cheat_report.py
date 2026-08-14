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
EDITABLE = ["model/pstore.py", "runtime/pfx.py", "runtime/sch.py", "mem/pool.py"]


def bash() -> str:
    """A bash that can actually run the cheat scripts.

    On Windows the `bash` on PATH is usually the WSL stub, which exits without running
    anything when no distribution is installed; every cheat then silently no-ops and each
    one appears to trip the same assertions as the shipped tree.
    """
    for cand in (r"C:\Program Files\Git\bin\bash.exe",
                 r"C:\Program Files\Git\usr\bin\bash.exe"):
        if Path(cand).is_file():
            return cand
    found = shutil.which("bash")
    if found is None:
        raise SystemExit("no bash on PATH; cannot replay the cheat scripts")
    return found


def trial(script: Path | None):
    with tempfile.TemporaryDirectory() as tmp:
        app_live = Path(tmp) / "live"
        shutil.copytree(TASK / "environment" / "app_src", app_live)
        if script is not None:
            body = script.read_text().replace("/app", app_live.as_posix())
            play = Path(tmp) / script.name
            play.write_text(body, newline="\n")
            proc = subprocess.run([bash(), str(play)], capture_output=True, cwd=tmp)
            if proc.returncode != 0:
                print("  ! %s exited %d" % (script.name, proc.returncode), file=sys.stderr)
        app = Path(tmp) / "app"
        shutil.copytree(TASK / "tests" / "pristine", app)
        for rel in EDITABLE:
            if (app_live / rel).is_file():
                shutil.copyfile(app_live / rel, app / rel)
        out = Path(tmp) / "out.json"
        env = dict(os.environ)
        env.update({"APPDIR": str(app), "PYTHONDONTWRITEBYTECODE": "1"})
        subprocess.run([sys.executable, str(TASK / "tests" / "runner.py"), str(out)],
                       capture_output=True, env=env)
        env["RUN_OUT"] = str(out)
        env["CONF_JSON"] = str(TASK / "tests" / "engine.json")
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
