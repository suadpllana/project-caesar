"""Host emulation of the two-image trial, for a machine with no Docker daemon.

It reproduces what the platform does apart from the container boundary: stage the agent tree,
let a solution or a cheat script act on it, collect the five declared files, lay them over the
verifier's pristine copy, run the worker under the same wall clock, then run the sealed grader
and read the reward.

What it does NOT reproduce, and what only a container run proves: the privilege drop, the
root-owned 0700 reward channel and seal, and the reaping of survivors. Probes that attack those
are reported here as emulation-only. Every run works in its own temporary directory, so two of
them can never interleave (CLAUDE.md, publish-settle-order).

Usage:
    python authoring/pull-check-stale/host_trial.py oracle
    python authoring/pull-check-stale/host_trial.py nop
    python authoring/pull-check-stale/host_trial.py script cheat/cheat-no-stuck.sh
    python authoring/pull-check-stale/host_trial.py dir authoring/pull-check-stale/variants/x
"""

import json
import os
import re
import secrets
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
TASK = REPO / "tasks" / "pull-check-stale"
PARTS = ("keep.py", "mark.py", "hold.py", "step.py", "wake.py")


def settings():
    """The wall clock and the per-family count, read from the shipped test.sh."""
    text = (TASK / "tests" / "test.sh").read_text(encoding="utf-8")
    secs = int(re.search(r"^CLOCK=(\d+)", text, re.M).group(1))
    per = int(re.search(r"^PER_FAMILY=(\d+)", text, re.M).group(1))
    return secs, per


def stage(root):
    app = root / "app"
    shutil.copytree(TASK / "environment" / "app_src", app)
    (root / "work").mkdir()
    (root / "logs").mkdir()
    return app


def act(kind, arg, root, app):
    """Let the solution or a cheat script act on the staged tree, as the agent would."""
    if kind == "nop":
        return 0
    if kind == "dir":
        for part in PARTS:
            src = Path(arg) / part
            if src.is_file():
                shutil.copyfile(src, app / "eng" / part)
        return 0
    script = TASK / "solution" / "solve.sh" if kind == "oracle" else Path(arg)
    if not script.is_absolute():
        script = (REPO / script).resolve()
    if not script.is_file():
        raise SystemExit("no such script: %s" % script)
    # The script's own directory is copied whole, so `dirname $0` still finds the files it
    # ships beside itself; only the absolute /app in its body is redirected at the staged
    # tree. A relative path handed to a harness that chdirs is a silent no-op (CLAUDE.md).
    beside = root / "act"
    shutil.copytree(script.parent, beside)
    here = beside / script.name
    here.write_text(script.read_text(encoding="utf-8").replace("/app", str(app)),
                    encoding="utf-8", newline="\n")
    run = subprocess.run(["bash", str(here)], cwd=str(beside),
                         capture_output=True, text=True, timeout=600)
    if run.returncode != 0:
        print("   script stderr: %s" % run.stderr.strip()[-500:])
    return run.returncode


def trial(kind, arg, quiet=False):
    secs, per = settings()
    root = Path(tempfile.mkdtemp(prefix="pcs-trial-"))
    try:
        app = stage(root)
        status = act(kind, arg, root, app)
        if status != 0 and not quiet:
            print("   the acting script exited %s" % status)

        seed = secrets.token_hex(16)
        for where in (root / "logs", root / "work"):
            (where / "nonce").write_text(seed + "\n", encoding="utf-8", newline="\n")
            (where / "per").write_text("%d\n" % per, encoding="utf-8", newline="\n")

        env = dict(os.environ)
        env.update({
            "PCS_TESTS": str(TASK / "tests"),
            "PCS_SEAL": str(TASK / "tests" / "seal"),
            "PCS_WORK": str(root / "work"),
            "PCS_LOGS": str(root / "logs"),
            "PCS_SUB": str(app / "eng"),
            "PYTHONDONTWRITEBYTECODE": "1",
        })
        t0 = time.time()
        worker = subprocess.run(
            ["timeout", str(secs), sys.executable, str(TASK / "tests" / "worker.py"),
             "--out", str(root / "work" / "worker_out.json")],
            capture_output=True, text=True, env=env)
        spent = time.time() - t0
        grade = subprocess.run(
            [sys.executable, "-m", "pytest", str(TASK / "tests" / "test_outputs.py"),
             "-p", "no:cacheprovider", "-q", "--ctrf", str(root / "logs" / "ctrf.json")],
            capture_output=True, text=True, env=env, cwd=str(root))
        reward = 1 if worker.returncode == 0 and grade.returncode == 0 else 0
        if not quiet:
            print("   worker exit %s in %.1fs of %ds, grader exit %s"
                  % (worker.returncode, spent, secs, grade.returncode))
            if reward == 0:
                tail = [ln for ln in grade.stdout.splitlines() if ln.strip()][-14:]
                print("\n".join("      " + ln for ln in tail))
                if worker.stderr.strip():
                    print("      worker stderr: %s" % worker.stderr.strip()[-400:])
        return reward, spent, worker, grade
    finally:
        shutil.rmtree(root, ignore_errors=True)


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    kind = argv[1]
    arg = argv[2] if len(argv) > 2 else None
    print("== %s %s" % (kind, arg or ""))
    reward, spent, _w, _g = trial(kind, arg)
    print("   reward %d" % reward)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
