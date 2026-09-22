"""Shared plumbing for the authoring scripts of stale-cover-serve.

Every tree it builds goes into a temporary directory outside the bundle: an authoring run
that writes inside tasks/<slug>/ ends up inside the submission zip, which is how a 455-entry
archive once shipped.
"""
import importlib.util
import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
TASK = ROOT / "tasks" / "stale-cover-serve"
SRC = TASK / "environment" / "app_src"
SOL = TASK / "solution"
PARTS = ("seg.py", "pick.py", "hole.py", "mend.py", "knit.py", "age.py", "ask.py")

_ROOMS = []


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def gen():
    return load("gen", TASK / "tests" / "gen.py")


def cases():
    return load("cases", TASK / "tests" / "cases.py")


def model():
    return load("model", TASK / "tests" / "seal" / "model.py")


def tree(policy=None, files=None):
    """A copy of the shipped tree with a policy directory, then `files`, laid over it."""
    room = pathlib.Path(tempfile.mkdtemp(prefix="scs-"))
    _ROOMS.append(room)
    here = room / "app"
    shutil.copytree(SRC, here)
    if policy is not None:
        for part in PARTS:
            one = pathlib.Path(policy) / part
            if one.is_file():
                shutil.copy(one, here / "rng" / part)
    for name, src in (files or {}).items():
        (here / "rng" / name).write_text(src, encoding="utf-8", newline="\n")
    return here


def driver(here):
    """Import run_rng out of one tree, with the module cache purged first.

    Several trees carry a package of the same name, so a stale entry in sys.modules is a
    reading that silently grades as the reference.
    """
    for name in [n for n in sys.modules if n == "run_rng" or n == "rng" or
                 n.startswith("rng.")]:
        del sys.modules[name]
    sys.path.insert(0, str(here))
    try:
        return load("run_rng", pathlib.Path(here) / "run_rng.py")
    finally:
        sys.path.remove(str(here))


def run_text(here, text):
    mod = driver(here)
    return mod.run(text if text.endswith("\n") else text + "\n")


def clean():
    for room in _ROOMS:
        shutil.rmtree(room, ignore_errors=True)
    del _ROOMS[:]
