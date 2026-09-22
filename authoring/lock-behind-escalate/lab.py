#!/usr/bin/env python3
"""Shared helpers for this task's authoring scripts. Never ships.

Every tree it builds goes to a temporary directory outside the bundle, and importing the
bundle's own modules leaves no __pycache__ inside tasks/<slug>/: authoring scratch that lands
in the task folder has been packaged before (CLAUDE.md).
"""
import sys as _sys

_sys.dont_write_bytecode = True

import importlib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
TASK = ROOT / "tasks" / "lock-behind-escalate"
SOL = TASK / "solution"
SRC = TASK / "environment" / "app_src"
PARTS = ("held.py", "wait.py", "grant.py", "esc.py", "dead.py", "settle.py")


def tree(policy=None, files=None):
    """A fresh copy of the shipped tree with one set of the six files laid over it."""
    room = Path(tempfile.mkdtemp(prefix="lbe-"))
    here = room / "app"
    shutil.copytree(SRC, here, ignore=shutil.ignore_patterns("__pycache__"))
    if policy is not None:
        for part in PARTS:
            shutil.copy(Path(policy) / part, here / "lm" / part)
    if files is not None:
        for part, text in files.items():
            (here / "lm" / part).write_text(text, encoding="utf-8", newline="\n")
    return here


def inproc(here):
    """Import run_lm out of `here`, dropping any previously imported copy."""
    for name in [n for n in sys.modules if n == "run_lm" or n == "lm" or n.startswith("lm.")]:
        del sys.modules[name]
    sys.path.insert(0, str(here))
    try:
        return importlib.import_module("run_lm")
    finally:
        sys.path.remove(str(here))


def run_text(here, text):
    """Run one script in this process. Fast, and safe for semantic variants only."""
    mod = inproc(here)
    try:
        return mod.run(text)
    except Exception as exc:  # a wrong reading may well blow up
        return ["RAISED", type(exc).__name__]


def run_shell(here, text, timeout=120):
    """Run one script in a subprocess, for anything that might not come back."""
    room = Path(tempfile.mkdtemp(prefix="lbe-prog-"))
    prog = room / "p.txt"
    prog.write_text(text.rstrip("\n") + "\n", encoding="utf-8", newline="\n")
    try:
        done = subprocess.run([sys.executable, "run_lm.py", str(prog)], cwd=str(here),
                              capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return ["TIMEOUT"]
    finally:
        shutil.rmtree(room, ignore_errors=True)
    if done.returncode != 0:
        tail = done.stderr.strip().splitlines()[-1:] or ["exit %d" % done.returncode]
        return ["RAISED", tail[0]]
    return done.stdout.splitlines()


def sealed():
    """The sealed model and the shipped case list and generator."""
    for p in (str(TASK / "tests"), str(TASK / "tests" / "seal")):
        if p not in sys.path:
            sys.path.insert(0, p)
    import cases
    import gen
    import model
    return cases, gen, model
