"""Assemble a tree - the shipped one, with a set of replacement parts laid over it - and run
programs through it in this process.

Every authoring script writes into a fresh temporary directory outside the bundle, because a
scratch directory inside the task folder ships (CLAUDE.md, token-seam-emit).
"""

import pathlib
import shutil
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
TASK = ROOT / "tasks" / "entry-lift-restate"
PARTS = ("book.py", "sect.py", "step.py", "gate.py", "wake.py", "walk.py", "tell.py")


def build(*over):
    """A copy of the shipped tree with the .py files of each `over` directory laid on top."""
    room = pathlib.Path(tempfile.mkdtemp(prefix="elr-"))
    here = room / "app"
    shutil.copytree(TASK / "environment" / "app_src", here)
    for src in over:
        src = pathlib.Path(src)
        for part in PARTS:
            one = src / part
            if one.is_file():
                shutil.copy(one, here / "cf" / part)
    return here


def loader(here):
    """Import `run_conf` out of `here`, with any previous tree's modules discarded."""
    for name in list(sys.modules):
        if name == "run_conf" or name == "cf" or name.startswith("cf."):
            del sys.modules[name]
    sys.path.insert(0, str(here))
    try:
        import run_conf
    finally:
        sys.path.remove(str(here))
    return run_conf


def shipped():
    return loader(build())


def reference():
    return loader(build(TASK / "solution"))
