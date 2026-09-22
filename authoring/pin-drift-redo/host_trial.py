"""Host emulation of the trial: stage /app and /tests, then run the shipped tests/test.sh.

Docker has no daemon in this workspace, so the two containers are emulated by the real
absolute paths the harness uses. What this does exercise, because the shipped script does it
unchanged: the reward channel locked root-only before anything submitted runs, the sealed
directory at 0700, the privilege drop to uid 1002, the wall clock, the session, the reap, and
the reward written last by the root half. What it does not exercise is container isolation
itself - one kernel namespace, one filesystem, the host's python. Results from here are host
emulation and are reported as that, never as container evidence.

/app, /tests, /work and /logs are fixed paths, so two runs at once would read each other's
files: this takes a lock.

    python3 host_trial.py --dir tasks/pin-drift-redo/solution      the oracle
    python3 host_trial.py --nop                                    the shipped tree
    python3 host_trial.py --cheat tasks/pin-drift-redo/cheat/x.sh  one cheat
    python3 host_trial.py --all-cheats
"""
from __future__ import annotations

import argparse
import fcntl
import json
import os
import pwd
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
TASK = ROOT / "tasks" / "pin-drift-redo"
SRC = TASK / "environment" / "app_src"
TESTS = TASK / "tests"
PARTS = ("ver.py", "take.py", "hold.py", "work.py", "step.py", "close.py")
APP = Path("/app")
LIVE_TESTS = Path("/tests")
WORK = Path("/work")
LOGS = Path("/logs")
LOCK = Path("/tmp/pin-drift-redo.trial.lock")
SANDBOX_UID = 1002


def sandbox_user():
    try:
        pwd.getpwuid(SANDBOX_UID)
    except KeyError:
        subprocess.run(["useradd", "--no-create-home", "--uid", str(SANDBOX_UID), "sandbox"],
                       check=True, capture_output=True)


def stage(over: Path | None, cheat: Path | None):
    for path in (APP, LIVE_TESTS, WORK, LOGS):
        if path.exists():
            shutil.rmtree(path, ignore_errors=True)
    shutil.copytree(SRC, APP)
    shutil.copytree(TESTS, LIVE_TESTS)
    for stale in LIVE_TESTS.rglob("__pycache__"):
        shutil.rmtree(stale, ignore_errors=True)
    LOGS.mkdir(parents=True, exist_ok=True)
    subprocess.run(["chmod", "-R", "a+rX", str(LIVE_TESTS), str(APP)], check=True)
    if over is not None:
        for part in PARTS:
            one = Path(over) / part
            if one.is_file():
                shutil.copy(one, APP / "led" / part)
    if cheat is not None:
        done = subprocess.run(["bash", str(Path(cheat).resolve())], cwd=str(APP),
                              capture_output=True, text=True, timeout=1800)
        if done.returncode != 0:
            return "cheat script exited %d: %s" % (done.returncode, done.stderr.strip()[-300:])
    return None


def trial(over: Path | None = None, cheat: Path | None = None):
    sandbox_user()
    with open(LOCK, "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        note = stage(over, cheat)
        started = time.perf_counter()
        done = subprocess.run(["bash", "/tests/test.sh"], capture_output=True, text=True,
                              timeout=3600)
        spent = time.perf_counter() - started
        reward = None
        got = LOGS / "verifier" / "reward.txt"
        if got.is_file():
            reward = got.read_text(encoding="utf-8").strip()
        return {"reward": reward, "test_sh": done.returncode, "seconds": round(spent, 2),
                "note": note, "out": done.stdout.strip()[-2500:],
                "err": done.stderr.strip()[-800:]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir")
    ap.add_argument("--cheat")
    ap.add_argument("--nop", action="store_true")
    ap.add_argument("--all-cheats", action="store_true")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    if args.all_cheats:
        bad = []
        for one in sorted((TASK / "cheat").glob("*.sh")):
            got = trial(cheat=one)
            if got["reward"] != "0":
                bad.append(one.name)
            print("%s %-32s reward=%s %5.1fs %s" %
                  ("OK  " if got["reward"] == "0" else "PASS", one.name, got["reward"],
                   got["seconds"], got["note"] or ""), flush=True)
        print("\n%d cheat(s) did not score 0: %s" % (len(bad), bad))
        return 1 if bad else 0

    over = Path(args.dir).resolve() if args.dir else None
    cheat = Path(args.cheat).resolve() if args.cheat else None
    got = trial(over=over, cheat=cheat)
    print(json.dumps({k: got[k] for k in ("reward", "test_sh", "seconds", "note")}))
    if got["reward"] != "1" or args.verbose:
        print(got["out"])
        if got["err"]:
            print("stderr:", got["err"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
