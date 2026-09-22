#!/usr/bin/env python3
"""Shared helpers for this task's authoring scripts. Never ships.

Every tree it builds goes to a temporary directory outside the bundle: a stray scratch
directory inside tasks/<slug>/ has been packaged before (CLAUDE.md, token-seam-emit).
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
TASK = ROOT / "tasks" / "owed-check-rewind"
SOL = TASK / "solution"
SRC = TASK / "environment" / "app_src"
HERE = Path(__file__).resolve().parent
PARTS = ("heap.py", "act.py", "chk.py", "owe.py", "sp.py", "sess.py")


def tree(policy=None, files=None):
    """A fresh copy of the shipped tree with one set of tx files laid over it."""
    room = Path(tempfile.mkdtemp(prefix="ocr-"))
    here = room / "app"
    shutil.copytree(SRC, here)
    if policy is not None:
        for part in PARTS:
            src = Path(policy) / part
            if src.is_file():
                shutil.copy(src, here / "tx" / part)
    if files is not None:
        for part, text in files.items():
            (here / "tx" / part).write_text(text, encoding="utf-8", newline="\n")
    return here


def inproc(here):
    """Import run_tx out of `here`, dropping any previously imported copy."""
    for name in [n for n in sys.modules if n == "run_tx" or n == "tx" or n.startswith("tx.")]:
        del sys.modules[name]
    sys.path.insert(0, str(here))
    try:
        return importlib.import_module("run_tx")
    finally:
        sys.path.remove(str(here))


def run_text(here, text):
    """Run one program in this process. Fast, and safe for semantic variants only."""
    mod = inproc(here)
    try:
        return mod.run(text)
    except Exception as exc:  # a wrong reading may well blow up
        return ["RAISED", type(exc).__name__, str(exc)[:80]]


def run_shell(here, text, timeout=300):
    """Run one program in a subprocess, for anything that might not come back."""
    room = Path(tempfile.mkdtemp(prefix="ocr-prog-"))
    prog = room / "p.txt"
    prog.write_text(text.rstrip("\n") + "\n", encoding="utf-8", newline="\n")
    try:
        done = subprocess.run([sys.executable, "run_tx.py", str(prog)], cwd=str(here),
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
    """The sealed model and the shipped case list and generator."""
    sys.path.insert(0, str(TASK / "tests"))
    sys.path.insert(0, str(TASK / "tests" / "seal"))
    import gen
    import model
    try:
        import cases
    except ImportError:
        cases = None
    return cases, gen, model
