#!/usr/bin/env python3
"""Shared helpers for this task's authoring scripts. Never ships.

Every tree it builds goes to a temporary directory outside the bundle: authoring scratch that
lands inside tasks/<slug>/ has been packaged before (CLAUDE.md, token-seam-emit).
"""
import sys as _sys

# Importing the bundle's own modules must not leave a __pycache__ inside tasks/<slug>/.
_sys.dont_write_bytecode = True

import importlib  # noqa: E402
import shutil  # noqa: E402
import subprocess  # noqa: E402
import sys  # noqa: E402
import tempfile  # noqa: E402
from pathlib import Path  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent.parent
TASK = ROOT / "tasks" / "restate-hold-plan"
SOL = TASK / "solution"
SRC = TASK / "environment" / "app_src"
PARTS = ("keep.py", "reach.py", "look.py", "settle.py", "order.py")


def tree(policy=None, files=None):
    """A fresh copy of the shipped tree with one set of planner files laid over it."""
    room = Path(tempfile.mkdtemp(prefix="rhp-"))
    here = room / "app"
    shutil.copytree(SRC, here)
    if policy is not None:
        for part in PARTS:
            src = Path(policy) / part
            if src.is_file():
                shutil.copy(src, here / "plan" / part)
    if files is not None:
        for part, text in files.items():
            (here / "plan" / part).write_text(text, encoding="utf-8", newline="\n")
    return here


def inproc(here):
    """Import run_plan out of `here`, dropping any previously imported copy."""
    for name in [n for n in sys.modules
                 if n == "run_plan" or n == "plan" or n.startswith("plan.")]:
        del sys.modules[name]
    sys.path.insert(0, str(here))
    try:
        return importlib.import_module("run_plan")
    finally:
        sys.path.remove(str(here))


def run_text(here, text):
    """Run one pipeline in this process. Fast, and safe for semantic variants only."""
    mod = inproc(here)
    try:
        return mod.run(text)
    except Exception as exc:  # a wrong reading may well blow up
        return ["RAISED", type(exc).__name__]


def run_shell(here, text, timeout=120):
    """Run one pipeline in a subprocess, for anything that might not come back."""
    room = Path(tempfile.mkdtemp(prefix="rhp-prog-"))
    prog = room / "p.txt"
    prog.write_text(text.rstrip("\n") + "\n", encoding="utf-8", newline="\n")
    try:
        done = subprocess.run([sys.executable, "run_plan.py", str(prog)], cwd=str(here),
                              capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return ["TIMEOUT"]
    finally:
        shutil.rmtree(room, ignore_errors=True)
    if done.returncode != 0:
        tail = done.stderr.strip().splitlines()[-1:]
        return ["RAISED", tail[0] if tail else "exit %d" % done.returncode]
    return done.stdout.splitlines()


def sealed():
    """The sealed model and the shipped case list and generator."""
    for p in (str(TASK / "tests" / "seal"), str(TASK / "tests")):
        if p not in sys.path:
            sys.path.insert(0, p)
    import cases
    import gen
    import model
    return cases, gen, model
