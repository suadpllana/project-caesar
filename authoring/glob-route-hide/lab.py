#!/usr/bin/env python3
"""Shared helpers for this task's authoring scripts. Never ships.

Every tree built here goes to a temporary directory outside the bundle, and importing the
bundle's modules writes no bytecode, so no authoring scratch can land inside tasks/<slug>/.
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
TASK = ROOT / "tasks" / "glob-route-hide"
SOL = TASK / "solution"
SRC = TASK / "environment" / "app_src"
PARTS = ("vis.py", "own.py", "glob.py", "fix.py", "say.py")


def tree(policy=None, files=None):
    """A fresh copy of the shipped tree with one set of resolution files laid over it."""
    room = Path(tempfile.mkdtemp(prefix="grh-"))
    here = room / "app"
    shutil.copytree(SRC, here, ignore=shutil.ignore_patterns("__pycache__"))
    if policy is not None:
        for part in PARTS:
            src = Path(policy) / part
            if src.is_file():
                shutil.copy(src, here / "fe" / part)
    if files is not None:
        for part, text in files.items():
            (here / "fe" / part).write_text(text, encoding="utf-8", newline="\n")
    return here


def drop(here):
    shutil.rmtree(Path(here).parent, ignore_errors=True)


def inproc(here):
    """Import run_res out of `here`, dropping any previously imported copy."""
    for name in [n for n in sys.modules if n == "run_res" or n == "fe" or n.startswith("fe.")]:
        del sys.modules[name]
    sys.path.insert(0, str(here))
    try:
        return importlib.import_module("run_res")
    finally:
        sys.path.remove(str(here))


def run_text(here, text):
    """Run one program in this process. Fast, and fit for semantic variants only."""
    mod = inproc(here)
    try:
        return mod.run(text)
    except Exception as exc:
        return ["RAISED", type(exc).__name__]


def run_shell(here, text, timeout=120):
    """Run one program in a subprocess, for anything that might not come back."""
    room = Path(tempfile.mkdtemp(prefix="grh-prog-"))
    prog = room / "p.txt"
    prog.write_text(text.rstrip("\n") + "\n", encoding="utf-8", newline="\n")
    try:
        done = subprocess.run([sys.executable, "run_res.py", str(prog)], cwd=str(here),
                              capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return ["TIMEOUT"]
    finally:
        shutil.rmtree(room, ignore_errors=True)
    if done.returncode != 0:
        tail = done.stderr.strip().splitlines()
        return ["RAISED", tail[-1] if tail else "exit %d" % done.returncode]
    return done.stdout.splitlines()


def sealed():
    """The sealed model with the shipped case list and generator."""
    for p in (str(TASK / "tests"), str(TASK / "tests" / "seal")):
        if p not in sys.path:
            sys.path.insert(0, p)
    import cases
    import gen
    import model
    return cases, gen, model
