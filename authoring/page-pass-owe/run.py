#!/usr/bin/env python3
"""Assemble a runnable tree from the frozen environment plus a set of module files.

Nothing is written inside tasks/page-pass-owe: the tree is built in a fresh temp dir
outside the bundle, because authoring scratch left in the task folder ships.

    python3 authoring/page-pass-owe/run.py <lists...>              reference modules
    python3 authoring/page-pass-owe/run.py --broken <lists...>     shipped modules
    python3 authoring/page-pass-owe/run.py --from DIR <lists...>   any module dir
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
TASK = ROOT / "tasks" / "page-pass-owe"
PARTS = ("seq", "scr", "owe", "pg", "edt", "rep")


def build(src: Path) -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="ppo-"))
    shutil.copytree(TASK / "environment" / "app_src", tmp / "app")
    for part in PARTS:
        shutil.copyfile(src / (part + ".py"), tmp / "app" / "lst" / (part + ".py"))
    return tmp


def run(tree: Path, path: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-u", "run_lst.py", path],
        cwd=str(tree / "app"), capture_output=True, text=True,
    )


def main(argv):
    src = TASK / "solution"
    args = list(argv)
    if args and args[0] == "--broken":
        src = TASK / "environment" / "app_src" / "lst"
        args = args[1:]
    elif len(args) >= 2 and args[0] == "--from":
        src = Path(args[1]).resolve()
        args = args[2:]
    tree = build(src)
    try:
        for path in args:
            done = run(tree, str(Path(path).resolve()))
            sys.stdout.write(done.stdout)
            if done.returncode != 0:
                sys.stderr.write(done.stderr)
                return done.returncode
    finally:
        shutil.rmtree(tree, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
