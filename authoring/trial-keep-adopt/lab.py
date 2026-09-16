"""Lay a set of six files over a fresh copy of the shipped tree and run programs through it.

Every authoring script goes through here, and every copy is made under tempfile.mkdtemp outside
the bundle, because an authoring run that writes inside tasks/<slug>/ ships (CLAUDE.md).
"""
import importlib
import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
TASK = ROOT / "tasks" / "trial-keep-adopt"
SRC = TASK / "environment" / "app_src"
PARTS = ("keep.py", "look.py", "make.py", "need.py", "feed.py", "hold.py")


def tree(over=None):
    room = pathlib.Path(tempfile.mkdtemp(prefix="tka-"))
    here = room / "app"
    shutil.copytree(SRC, here)
    if over is not None:
        for part in PARTS:
            one = pathlib.Path(over) / part
            if one.is_file():
                shutil.copy(one, here / "fld" / part)
    return here


def load(here):
    for name in list(sys.modules):
        if name == "ops" or name == "fld" or name.startswith("fld."):
            del sys.modules[name]
    sys.path.insert(0, str(here))
    ops = importlib.import_module("ops")
    prog = importlib.import_module("fld.prog")
    store = importlib.import_module("fld.store")
    return ops, prog, store


def trace(here, lines):
    ops, prog, store = load(here)
    f = store.Fld()
    for w in prog.walk(lines):
        ops.ex(f, w)
    return f.out


def ref():
    return tree(TASK / "solution")


def shipped():
    return tree(None)


def run(here, prog, timeout=120):
    """Drive one program file through a tree in a fresh process, so a hang is a timeout."""
    proc = subprocess.run([sys.executable, "run_fld.py", str(prog)], cwd=str(here),
                          capture_output=True, text=True, timeout=timeout)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip())
    return proc.stdout.splitlines()
