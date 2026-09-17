"""A two-stage trial on the host, for a machine where the images cannot be pulled.

This is the emulation, not the container run, and it is honest about the difference: it lays
the environment tree at /app, the verifier at /tests, and runs the shipped `tests/test.sh`
unchanged, so the privilege drop, the locked reward channel, the session, the wall clock, the
reaper and the grader all run exactly as they will on the platform. What it does not prove is
anything about the images themselves - the base, the pinned packages, the COPY lines - which is
what `tools/imagecheck.py` covers and what `tools/docker_trial.py` would cover with a registry.

It writes absolute paths, so two copies running side by side are one run with the rows
interleaved. It takes a lock.

    python3 -u host_trial.py oracle
    python3 -u host_trial.py nop
    python3 -u host_trial.py --all
    python3 -u host_trial.py --variants
    python3 -u host_trial.py --cheat cheat/cheat-lift-all.sh
    python3 -u host_trial.py --dir ../variants/ok-flat
"""
import fcntl
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
TASK = ROOT / "tasks" / "still-graft-charge"
PARTS = ("cell.py", "hold.py", "cost.py", "tree.py", "gate.py", "free.py")
LOCK = Path("/tmp/still-graft-charge.trial.lock")


def lay():
    """The agent's tree at /app and the verifier's at /tests, as the two images hold them."""
    for path in (Path("/app"), Path("/tests"), Path("/work"), Path("/logs")):
        if path.exists():
            shutil.rmtree(path, ignore_errors=True)
    shutil.copytree(TASK / "environment" / "app_src", "/app")
    shutil.copytree(TASK / "tests", "/tests")
    Path("/logs/verifier").mkdir(parents=True, exist_ok=True)


def agent(script):
    """Run one agent script with the tree in place, and report if it failed outright."""
    if script is None:
        return
    one = Path(script).resolve()
    if not one.is_file():
        raise SystemExit("no such agent script: %s" % one)
    proc = subprocess.run(["bash", str(one)], cwd="/app", capture_output=True, text=True)
    if proc.returncode != 0:
        print("    agent script exited %d: %s" % (proc.returncode, proc.stderr[-300:].strip()))


def verify():
    proc = subprocess.run(["bash", "/tests/test.sh"], capture_output=True, text=True)
    text = proc.stdout + proc.stderr
    try:
        reward = int(Path("/logs/verifier/reward.txt").read_text().strip() or 0)
    except (OSError, ValueError):
        reward = 0
    tail = [one for one in text.splitlines() if "passed" in one or "failed" in one
            or "error" in one.lower()]
    if tail:
        print("    " + tail[-1].strip()[:160])
    return reward


def one(name, script, want):
    print("[%s]" % name)
    start = time.time()
    lay()
    agent(script)
    reward = verify()
    ok = reward == want
    print("    reward=%d expected=%d -> %s  (%.0fs)\n"
          % (reward, want, "PASS" if ok else "FAIL", time.time() - start))
    return ok


def from_dir(d):
    """Turn a directory of the six files into an agent script."""
    d = Path(d).resolve()
    lines = ["#!/bin/bash", "set -euo pipefail", ""]
    for part in PARTS:
        lines.append('cp %s /app/led/%s' % (d / part, part))
    out = Path("/tmp/sgc-variant.sh")
    out.write_text("\n".join(lines) + "\n")
    return out


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    with open(LOCK, "w") as fh:
        try:
            fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            raise SystemExit("another trial is running: %s" % LOCK)
        what = argv[1]
        if what == "oracle":
            return 0 if one("oracle", TASK / "solution" / "solve.sh", 1) else 1
        if what == "nop":
            return 0 if one("nop", None, 0) else 1
        if what == "--cheat":
            path = Path(argv[2])
            if not path.is_absolute():
                path = TASK / path
            return 0 if one("cheat: " + path.name, path, 0) else 1
        if what == "--dir":
            d = Path(argv[2])
            return 0 if one("variant: " + d.name, from_dir(d), 1) else 1
        if what == "--variants":
            res = []
            for d in sorted((HERE / "variants").iterdir()):
                if d.is_dir() and d.name.startswith("ok-"):
                    res.append(one("variant: " + d.name, from_dir(d), 1))
            print("%d/%d variants scored 1" % (sum(res), len(res)))
            return 0 if all(res) else 1
        if what == "--all":
            res = [one("oracle", TASK / "solution" / "solve.sh", 1), one("nop", None, 0)]
            for cheat in sorted((TASK / "cheat").glob("*.sh")):
                res.append(one("cheat: " + cheat.name, cheat, 0))
            print("%d/%d trials behaved as required" % (sum(res), len(res)))
            return 0 if all(res) else 1
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
