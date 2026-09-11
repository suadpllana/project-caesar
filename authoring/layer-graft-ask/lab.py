"""Assemble a runnable tree outside the bundle and run a plan through it.

Usage:
    python authoring/layer-graft-ask/lab.py <plan-file> [--src DIR ...]

The frozen files come from the task's environment; the six editable files come from
`solution/` unless a `--src` directory supplies its own copy (later ones win). Everything is
staged in a fresh temp directory so no authoring run can ever leave a file inside the bundle.
"""
import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
TASK = ROOT / "tasks" / "layer-graft-ask"
PARTS = ("pile", "past", "made", "roll", "work", "ans")


def stage(srcs, into=None):
    work = Path(into or tempfile.mkdtemp(prefix="lgalab-"))
    shutil.copytree(TASK / "environment" / "app_src", work, dirs_exist_ok=True)
    for src in srcs:
        src = Path(src)
        for part in PARTS:
            cand = src / (part + ".py")
            if cand.exists():
                shutil.copy(cand, work / "cfg" / (part + ".py"))
    return work


def run(work, plan, timeout=600):
    return subprocess.run(
        [sys.executable, "run_plan.py", str(Path(plan).resolve())],
        cwd=str(work), capture_output=True, text=True, timeout=timeout)


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("plan")
    ap.add_argument("--src", action="append", default=[])
    ap.add_argument("--shipped", action="store_true")
    args = ap.parse_args(argv[1:])
    srcs = [] if args.shipped else [TASK / "solution"]
    srcs += args.src
    work = stage(srcs)
    got = run(work, args.plan)
    sys.stdout.write(got.stdout)
    sys.stderr.write(got.stderr)
    shutil.rmtree(work, ignore_errors=True)
    return got.returncode


if __name__ == "__main__":
    sys.exit(main(sys.argv))
