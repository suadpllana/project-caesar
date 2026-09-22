#!/usr/bin/env python3
"""Shared helpers for this task's authoring scripts. Never ships.

Every tree it builds goes to a temporary directory outside the bundle: a stray scratch
directory inside tasks/<slug>/ has been packaged before (CLAUDE.md, token-seam-emit).
"""
import sys as _sys

# Importing the bundle's own modules must not leave a __pycache__ inside tasks/<slug>/.
_sys.dont_write_bytecode = True

import importlib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
HERE = Path(__file__).resolve().parent
TASK = ROOT / "tasks" / "anchor-band-settle"
SOL = TASK / "solution"
SRC = TASK / "environment" / "app_src"
PARTS = ("lay.py", "stick.py", "pick.py", "hold.py")


def tree(policy=None, files=None):
    """A fresh copy of the shipped tree with one set of the four files laid over it."""
    room = Path(tempfile.mkdtemp(prefix="abs-"))
    here = room / "app"
    shutil.copytree(SRC, here)
    if policy is not None:
        for part in PARTS:
            src = Path(policy) / part
            if src.is_file():
                shutil.copy(src, here / "view" / part)
    if files is not None:
        for part, text in files.items():
            (here / "view" / part).write_text(text, encoding="utf-8", newline="\n")
    return here


def inproc(here):
    """Import view.frame out of `here`, dropping any previously imported copy."""
    for name in [n for n in sys.modules if n == "view" or n.startswith("view.")
                 or n == "run_view"]:
        del sys.modules[name]
    sys.path.insert(0, str(here))
    try:
        return importlib.import_module("view.frame")
    finally:
        sys.path.remove(str(here))


def run_text(here, text):
    """Run one program in this process. Fast, and safe for semantic variants only."""
    mod = inproc(here)
    try:
        return mod.run(text)
    except Exception as exc:  # a wrong reading may well blow up
        return ["RAISED", "%s: %s" % (type(exc).__name__, exc)]


def run_shell(here, text, timeout=600):
    """Run one program in a subprocess, for anything that might not come back."""
    room = Path(tempfile.mkdtemp(prefix="abs-prog-"))
    prog = room / "p.txt"
    prog.write_text(text.rstrip("\n") + "\n", encoding="utf-8", newline="\n")
    try:
        done = subprocess.run([sys.executable, "run_view.py", str(prog)], cwd=str(here),
                              capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return ["TIMEOUT"]
    finally:
        shutil.rmtree(room, ignore_errors=True)
    if done.returncode != 0:
        tail = done.stderr.strip().splitlines()
        return ["RAISED", tail[-1] if tail else "exit %d" % done.returncode]
    return done.stdout.splitlines()


def naive():
    sys.path.insert(0, str(HERE))
    import naive as mod
    return mod


def sealed():
    """The sealed model and the shipped case list and generator."""
    for p in (str(TASK / "tests" / "seal"), str(TASK / "tests")):
        if p not in sys.path:
            sys.path.insert(0, p)
    import cases
    import gen
    import model
    return cases, gen, model
