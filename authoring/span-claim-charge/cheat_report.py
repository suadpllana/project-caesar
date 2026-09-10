"""Run every cheat locally and say which test catches it.

Host emulation, not the container: it proves what a reading does to the traces, and it is
the fast loop. The isolation probes are only truly exercised by tools/docker_trial.py,
which drops privileges and locks the reward channel; here they are expected to score 0 and
the reason is reported so a probe that quietly stopped attacking is visible.

A cheat that is caught reports the case that caught it. A cheat that is not caught by any
trace is timed against the big families instead, because the correct-and-too-slow ones can
only be caught by the limit.
"""
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import time

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
TASK = ROOT / "tasks" / "span-claim-charge"
sys.path.insert(0, str(TASK / "tests"))
sys.path.insert(0, str(TASK / "tests" / "seal"))

import cases  # noqa: E402
import gen  # noqa: E402
import model  # noqa: E402

PARTS = ("dev.py", "hold.py", "item.py", "line.py", "tally.py")
APP = pathlib.Path("/app")
LOCK = pathlib.Path("/tmp/span-claim-charge.trial.lock")
LIMIT = 60
GT = json.loads((TASK / "tests" / "seal" / "gt.json").read_text(encoding="utf-8"))


def lay_app():
    if APP.exists():
        shutil.rmtree(APP)
    shutil.copytree(TASK / "environment" / "app_src", APP,
                    ignore=shutil.ignore_patterns("__pycache__"))


def stage():
    room = pathlib.Path(tempfile.mkdtemp())
    tree = room / "app"
    shutil.copytree(TASK / "tests" / "pristine", tree,
                    ignore=shutil.ignore_patterns("__pycache__"))
    for part in PARTS:
        one = APP / "store" / part
        if one.is_file():
            shutil.copy(one, tree / "store" / part)
    return tree


def main():
    if LOCK.exists():
        print("another trial holds the lock")
        return 2
    LOCK.write_text(str(time.time()))
    only = sys.argv[1] if len(sys.argv) > 1 else ""
    try:
        rows = []
        for path in sorted((TASK / "cheat").glob("*.sh")):
            if only and only not in path.name:
                continue
            lay_app()
            proc = subprocess.run(["bash", str(path.resolve())],
                                  capture_output=True, text=True)
            if proc.returncode != 0:
                rows.append((path.name, "SCRIPT FAILED rc=%d %s"
                             % (proc.returncode, proc.stderr[-200:])))
                continue
            tree = stage()
            run = subprocess.run([sys.executable, str(HERE / "judge_one.py"), str(tree)],
                                 capture_output=True, text=True, timeout=600)
            shutil.rmtree(tree.parent, ignore_errors=True)
            verdict = run.stdout.strip().splitlines()
            verdict = verdict[-1] if verdict else (
                "caught by the record it never wrote (the probe exited the runner, rc=%d) %s"
                % (run.returncode, run.stderr[-120:]))
            print("%s %-34s %s" % ("  " if verdict.startswith("caught") else "**",
                                   path.name, verdict), flush=True)
            rows.append((path.name, verdict))
        for name, verdict in rows:
            flag = "  " if verdict.startswith("caught") else "**"
            print("%s %-34s %s" % (flag, name, verdict))
        loose = [n for n, v in rows if not v.startswith("caught")]
        print("\n%d cheats, %d caught by a trace, %d not: %s"
              % (len(rows), len(rows) - len(loose), len(loose), ", ".join(loose)))
    finally:
        LOCK.unlink(missing_ok=True)
        if APP.exists():
            shutil.rmtree(APP, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
