"""Run the verifier's own stages on this machine, without Docker.

Stages the submission the way `tests/test.sh` does - worker, then grader - but as one user in
a temporary directory, so it proves the wiring and the grading, never the isolation. The real
privilege drop, the locked reward channel and the root-owned answers are only exercised by
tools/docker_trial.py. A lock file keeps two of these from writing each other's paths.
"""

import argparse
import json
import os
import secrets
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
TASK = ROOT / "tasks" / "claim-raise-cut"
LOCK = Path(tempfile.gettempdir()) / "crc-host-trial.lock"


def hold():
    for _ in range(600):
        try:
            fd = os.open(str(LOCK), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode())
            os.close(fd)
            return
        except FileExistsError:
            time.sleep(0.5)
    raise SystemExit("another host trial holds %s" % LOCK)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sub", default=str(TASK / "solution"),
                    help="directory holding the five modules to grade")
    ap.add_argument("--per", type=int, default=40)
    ap.add_argument("--heavy", type=int, default=6)
    ap.add_argument("--limit", type=int, default=60)
    ap.add_argument("--script", default=None,
                    help="a cheat script to run instead of copying --sub")
    ap.add_argument("--json", default=None, help="write a machine-readable summary here")
    args = ap.parse_args()

    hold()
    try:
        room = Path(tempfile.mkdtemp(prefix="crc-trial-"))
        work = room / "work"
        logs = room / "logs"
        app = room / "app"
        work.mkdir()
        logs.mkdir()
        shutil.copytree(TASK / "environment" / "app_src", app,
                        ignore=shutil.ignore_patterns("__pycache__"))

        if args.script:
            # The scripts write to /app, the absolute path they have in the agent's container.
            # Point /app at this run's copy for the length of the script; the lock keeps two
            # runs from doing it at once, and a pre-existing /app is never touched.
            script = Path(args.script).resolve()
            link = Path("/app")
            if link.exists() or link.is_symlink():
                raise SystemExit("/app already exists; refusing to stage a cheat over it")
            link.symlink_to(app)
            try:
                got = subprocess.run(["bash", str(script)], cwd="/app",
                                     capture_output=True, text=True,
                                     env=dict(os.environ, CRC_LOGS=str(logs),
                                              CRC_WORK=str(work), CRC_TESTS=str(TASK / "tests")))
            finally:
                link.unlink()
            if got.returncode:
                print("cheat script exit %d: %s" % (got.returncode, got.stderr[-600:]))
                print("reward 0")
                if args.json:
                    Path(args.json).write_text(json.dumps(
                        {"reward": 0, "over": False, "worker": None, "failed": [],
                         "script": got.returncode}), encoding="utf-8")
                return 1
        else:
            for part in ("mark.py", "item.py", "wait.py", "cyc.py", "txn.py"):
                src = Path(args.sub) / part
                if src.is_file():
                    shutil.copyfile(src, app / "hold" / part)

        seed = secrets.token_hex(16)
        for name, value in (("nonce", seed), ("per", args.per), ("heavy", args.heavy)):
            (logs / name).write_text("%s\n" % value, encoding="utf-8", newline="\n")
            (work / name).write_text("%s\n" % value, encoding="utf-8", newline="\n")

        env = dict(os.environ,
                   CRC_TESTS=str(TASK / "tests"), CRC_WORK=str(work),
                   CRC_SUB=str(app / "hold"), CRC_SEAL=str(TASK / "tests" / "seal"),
                   CRC_LOGS=str(logs), PYTHONDONTWRITEBYTECODE="1")
        t0 = time.time()
        try:
            worker = subprocess.run(
                [sys.executable, str(TASK / "tests" / "worker.py"),
                 "--out", str(work / "worker_out.json")],
                capture_output=True, text=True, env=env, timeout=args.limit + 5)
        except subprocess.TimeoutExpired:
            print("worker killed at %ds" % (args.limit + 5))
            print("reward 0")
            if args.json:
                Path(args.json).write_text(json.dumps(
                    {"reward": 0, "over": True, "worker": None, "failed": []}), encoding="utf-8")
            return 1
        took = time.time() - t0
        over = took > args.limit
        if worker.returncode:
            print("worker exit %d\n%s" % (worker.returncode, worker.stderr[-1500:]))
        graded = subprocess.run(
            [sys.executable, "-m", "pytest", str(TASK / "tests" / "test_outputs.py"),
             "-p", "no:cacheprovider", "-q", "--tb=no", "-rf"],
            capture_output=True, text=True, env=env,
            cwd=str(TASK / "tests"))
        ok = worker.returncode == 0 and graded.returncode == 0 and not over
        print(graded.stdout[-3000:])
        if graded.returncode:
            print(graded.stderr[-1500:])
        print("worker %.2fs (limit %ds)%s" % (took, args.limit, "  OVER LIMIT" if over else ""))
        print("reward", 1 if ok else 0)
        if args.json:
            failed = []
            for line in graded.stdout.splitlines():
                if line.startswith("FAILED "):
                    failed.append(line.split()[1].split("::", 1)[-1])
            Path(args.json).write_text(json.dumps(
                {"reward": 1 if ok else 0, "over": over, "worker": worker.returncode,
                 "failed": failed, "took": round(took, 2)}), encoding="utf-8")
        return 0 if ok else 1
    finally:
        LOCK.unlink(missing_ok=True)


if __name__ == "__main__":
    sys.exit(main())
