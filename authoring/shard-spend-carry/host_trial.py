#!/usr/bin/env python3
"""Host emulation of the two-container trial, at the real absolute paths.

Docker is present in this session but no image can be pulled: the registry's blob CDN is
refused by the egress policy, so `tools/docker_trial.py` cannot build either image here. This
stands in for it. It lays the shipped tree at /app, the verifier at /tests, makes /work and
/logs/verifier, creates the sandbox uid, and runs `tests/test.sh` verbatim - so the privilege
drop, the locked reward channel, the sealed directory, the wall clock, the session and the
reaper are all exercised. What it does not reproduce is the container boundary itself and the
image build.

It takes a lock: two copies writing the same absolute paths would interleave their rows.

    python3 host_trial.py oracle
    python3 host_trial.py nop
    python3 host_trial.py --dir authoring/shard-spend-carry/slow
    python3 host_trial.py --cheat tasks/shard-spend-carry/cheat/cheat-map-order.sh
"""
import argparse
import fcntl
import os
import pathlib
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
TASK = ROOT / "tasks" / "shard-spend-carry"
PARTS = ("cell.py", "lay.py", "cut.py", "walk.py", "tick.py", "keep.py")
LOCK = pathlib.Path("/tmp/ssc-host-trial.lock")


def sh(cmd, **kw):
    return subprocess.run(cmd, shell=isinstance(cmd, str), capture_output=True, text=True, **kw)


def wipe():
    for p in ("/app", "/tests", "/work", "/logs"):
        q = pathlib.Path(p)
        if q.exists():
            sh(["chmod", "-R", "u+rwX", p])
            shutil.rmtree(p, ignore_errors=True)


def stage():
    shutil.copytree(TASK / "environment" / "app_src", "/app")
    shutil.copytree(TASK / "tests", "/tests")
    for junk in pathlib.Path("/tests").rglob("__pycache__"):
        shutil.rmtree(junk, ignore_errors=True)
    os.makedirs("/work", exist_ok=True)
    os.makedirs("/logs/verifier", exist_ok=True)
    os.chmod("/tests/test.sh", 0o755)
    if sh(["id", "-u", "sandbox"]).returncode != 0:
        sh(["useradd", "--create-home", "--uid", "1002", "sandbox"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", nargs="?", default="oracle",
                    choices=["oracle", "nop", "dir", "cheat"])
    ap.add_argument("--dir", default=None)
    ap.add_argument("--cheat", default=None)
    args = ap.parse_args()

    with open(LOCK, "w") as lk:
        fcntl.flock(lk, fcntl.LOCK_EX)
        wipe()
        stage()

        if args.cheat:
            script = pathlib.Path(args.cheat).resolve()
            run = sh(["bash", str(script)], cwd="/app")
            if run.returncode != 0:
                print("cheat script exited %d\n%s" % (run.returncode, run.stderr[-1500:]))
        elif args.dir or args.mode == "dir":
            src = pathlib.Path(args.dir).resolve()
            for part in PARTS:
                if (src / part).is_file():
                    shutil.copy(src / part, "/app/opt/" + part)
        elif args.mode == "oracle":
            src = TASK / "solution"
            run = sh(["bash", str(src / "solve.sh")], cwd="/app")
            if run.returncode != 0:
                print("solve.sh exited %d\n%s" % (run.returncode, run.stderr[-1500:]))
        # nop: leave the shipped tree exactly as it is

        out = sh(["bash", "/tests/test.sh"])
        reward = pathlib.Path("/logs/verifier/reward.txt")
        got = reward.read_text().strip() if reward.is_file() else "<absent>"
        tail = (out.stdout + out.stderr).strip().splitlines()
        print("\n".join(tail[-25:]))
        label = args.cheat or args.dir or args.mode
        print("== %s: reward %s (test.sh exit %d)" % (label, got, out.returncode))
        return 0 if got in ("0", "1") else 2


if __name__ == "__main__":
    sys.exit(main())
