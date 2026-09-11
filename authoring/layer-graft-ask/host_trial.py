"""Host emulation of the two verifier stages, for iteration only.

It runs the worker and then the grader with every path redirected into a fresh temp directory,
so several of these can run at once and none of them writes inside the bundle. What it does NOT
exercise is the isolation: the privilege drop, the locked reward channel and the root-only seal
are only real in the container, which is what `tools/docker_trial.py` runs.

Usage:
    host_trial.py --src tasks/layer-graft-ask/solution [--src DIR] [--per N] [--scale N]
    host_trial.py --shipped
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
TASK = ROOT / "tasks" / "layer-graft-ask"
PARTS = ("pile.py", "past.py", "made.py", "roll.py", "work.py", "ans.py")


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", action="append", default=[])
    ap.add_argument("--shipped", action="store_true")
    ap.add_argument("--per", type=int, default=40)
    ap.add_argument("--scale", type=int, default=3)
    ap.add_argument("--nonce", default="hosttrial")
    ap.add_argument("--wall", type=int, default=60)
    ap.add_argument("--keep", action="store_true")
    args = ap.parse_args(argv[1:])

    box = Path(tempfile.mkdtemp(prefix="lgatrial-"))
    work, logs, sub = box / "work", box / "logs", box / "sub"
    for d in (work, logs, sub):
        d.mkdir(parents=True)
    srcs = [TASK / "environment" / "app_src" / "cfg" if args.shipped else TASK / "solution"]
    srcs += [Path(s) for s in args.src]
    for src in srcs:
        for part in PARTS:
            if (src / part).exists():
                shutil.copy(src / part, sub / part)

    for name, value in (("nonce", args.nonce), ("per", args.per), ("scale", args.scale)):
        for target in (work, logs):
            (target / name).write_text("%s\n" % value, encoding="utf-8", newline="\n")

    env = dict(os.environ)
    env.update({"LGA_TESTS": str(TASK / "tests"), "LGA_WORK": str(work),
                "LGA_SUB": str(sub), "LGA_SEAL": str(TASK / "tests" / "seal"),
                "LGA_LOGS": str(logs), "PYTHONDONTWRITEBYTECODE": "1"})

    start = time.time()
    try:
        ran = subprocess.run([sys.executable, str(TASK / "tests" / "worker.py"),
                              "--out", str(work / "worker_out.json")],
                             capture_output=True, text=True, env=env, timeout=args.wall)
        code, err = ran.returncode, ran.stderr
    except subprocess.TimeoutExpired:
        code, err = 124, "killed at the %d second wall clock" % args.wall
    took = time.time() - start
    print("worker exit %d in %.2f s" % (code, took), flush=True)
    if code != 0:
        print(err[-2000:], flush=True)

    graded = subprocess.run([sys.executable, "-m", "pytest",
                             str(TASK / "tests" / "test_outputs.py"),
                             "-p", "no:cacheprovider", "-q"],
                            capture_output=True, text=True, env=env,
                            cwd=str(TASK / "tests"))
    tail = [l for l in graded.stdout.strip().split("\n") if l.strip()][-6:]
    print("grader exit %d" % graded.returncode, flush=True)
    for line in tail:
        print("   " + line[:300], flush=True)
    reward = 1 if (code == 0 and graded.returncode == 0) else 0
    print("reward %d" % reward, flush=True)
    if args.keep:
        print("kept %s" % box, flush=True)
    else:
        shutil.rmtree(box, ignore_errors=True)
    return 0 if reward else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
