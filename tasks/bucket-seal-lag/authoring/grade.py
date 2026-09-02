"""Run the real grader over a real report, the way test.sh does.

`trial.py` re-implements the comparison so it can say *why* a candidate failed,
which is what makes a cheat sweep readable. That leaves the file that actually
ships ungraded by anything, and a grader nobody runs is a grader nobody has
checked - the tree-comparison bug in `share-register-screen` passed for exactly
that long. So this drives the runner, lays the tree out the way `test.sh` does,
and hands the result to `pytest /tests/test_outputs.py`.

    python authoring/grade.py                 the reference, which must pass
    python authoring/grade.py --overlay none  the shipped tree, which must not
    python authoring/grade.py --book cheat/cheat-near-only.sh
"""

import argparse
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "authoring"))

import harness
import trial


def stage(overlay, book, n, nonce):
    work = pathlib.Path(tempfile.mkdtemp(prefix="bsl-grade-"))
    app = harness.tree(overlay)
    if book is not None:
        trial.apply(book, app)
    shutil.copytree(ROOT / "tests", work / "tests",
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "pristine"))
    shutil.copytree(ROOT / "environment" / "app_src", work / "pristine",
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    out = work / "out.json"
    env = dict(os.environ)
    env.update(APPDIR=str(app), RUN_NONCE=nonce, RUN_COUNT=str(n),
               PYTHONDONTWRITEBYTECODE="1")
    subprocess.run([sys.executable, str(work / "tests" / "runner.py"), str(out)],
                   env=env, capture_output=True, text=True, timeout=1800)
    return work, app, out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--overlay", default="solution")
    ap.add_argument("--book", default=None)
    ap.add_argument("--n", type=int, default=40)
    ap.add_argument("--nonce", default="grade")
    args = ap.parse_args(argv)

    overlay = None if args.overlay == "none" else str(ROOT / args.overlay)
    book = str(ROOT / args.book) if args.book else None
    work, app, out = stage(overlay, book, args.n, args.nonce)
    try:
        if not out.exists():
            print("the run produced no report at all")
            return 1
        env = dict(os.environ)
        env.update(RUN_OUT=str(out), APP_DIR=str(app), PRISTINE_DIR=str(work / "pristine"),
                   RUN_NONCE=args.nonce, RUN_COUNT=str(args.n),
                   PYTHONPATH=str(work / "tests"), PYTHONDONTWRITEBYTECODE="1")
        proc = subprocess.run([sys.executable, "-m", "pytest", "-q",
                               str(work / "tests" / "test_outputs.py")],
                              env=env, capture_output=True, text=True, timeout=1800)
        print(proc.stdout[-3000:])
        if proc.stderr.strip():
            print(proc.stderr[-1000:])
        print("reward", 1 if proc.returncode == 0 else 0)
        return 0
    finally:
        shutil.rmtree(app.parent, ignore_errors=True)
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
