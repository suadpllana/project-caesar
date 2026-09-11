#!/usr/bin/env python3
"""Run programs through the real frozen driver with a chosen set of opt/ files.

Authoring-side only; writes to a temp directory outside the bundle. Used to check the
reference against the independent per-slot model before anything is built in Docker.
"""
import argparse
import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
TASK = ROOT / "tasks" / "shard-spend-carry"
PARTS = ("cell.py", "lay.py", "cut.py", "walk.py", "tick.py", "keep.py")


def tree(over: pathlib.Path | None) -> pathlib.Path:
    room = pathlib.Path(tempfile.mkdtemp(prefix="ssc-"))
    here = room / "app"
    shutil.copytree(TASK / "environment" / "app_src", here)
    if over is not None:
        for part in PARTS:
            one = over / part
            if one.is_file():
                shutil.copy(one, here / "opt" / part)
    return here


def run(here: pathlib.Path, prog: pathlib.Path) -> list[str]:
    p = subprocess.run([sys.executable, str(here / "run_fit.py"), str(prog)],
                       capture_output=True, text=True)
    if p.returncode != 0:
        raise SystemExit("driver failed on %s:\n%s" % (prog, p.stderr[-2000:]))
    return p.stdout.splitlines()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("prog")
    ap.add_argument("--over", default=str(TASK / "solution"))
    args = ap.parse_args()
    over = None if args.over in ("", "none") else pathlib.Path(args.over)
    here = tree(over)
    for line in run(here, pathlib.Path(args.prog)):
        print(line)
    shutil.rmtree(here.parent, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
