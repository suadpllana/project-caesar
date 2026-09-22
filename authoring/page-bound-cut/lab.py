"""Shared plumbing for the authoring scripts of page-bound-cut.

Everything here writes outside the task folder: a policy directory is laid over a copy of the
shipped tree in a fresh temporary directory, so an authoring run in flight can never be picked
up by the packager.
"""
import importlib
import shutil
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
TASK = REPO / "tasks" / "page-bound-cut"
SOL = TASK / "solution"
SRC = TASK / "environment" / "app_src"
SEAL = TASK / "tests" / "seal"
PARTS = ("fit.py", "bound.py", "cut.py", "join.py", "step.py")


def sealed():
    """The sealed case table, generator and model, imported from tests/."""
    for path in (TASK / "tests", SEAL):
        if str(path) not in sys.path:
            sys.path.insert(0, str(path))
    import gen
    import model
    cases = importlib.import_module("cases") if (TASK / "tests" / "cases.py").is_file() else None
    return cases, gen, model


def tree(policy):
    """A runnable copy of the shipped tree with one policy directory laid over it."""
    room = Path(tempfile.mkdtemp(prefix="pbc-lab-"))
    here = room / "app"
    shutil.copytree(SRC, here)
    policy = Path(policy)
    for part in PARTS:
        one = policy / part
        if one.is_file():
            shutil.copyfile(one, here / "pg" / part)
    return here


def spill(files, where=None):
    """Write {filename: source} over a fresh copy of the reference policy."""
    room = Path(where or tempfile.mkdtemp(prefix="pbc-pol-"))
    room.mkdir(parents=True, exist_ok=True)
    for part in PARTS:
        shutil.copyfile(SOL / part, room / part)
    for name, body in files.items():
        (room / name).write_text(body, encoding="utf-8", newline="\n")
    return room


_LOADED = {}
_LIVE = None


def _names():
    return [k for k in list(sys.modules) if k == "pg" or k.startswith("pg.") or k == "run_idx"]


def _swap(key, here):
    """Park the modules of the policy now loaded and bring this one's forward."""
    global _LIVE
    if _LIVE == key:
        return _LOADED[key]["run_idx"]
    if _LIVE is not None:
        _LOADED[_LIVE] = {n: sys.modules.pop(n) for n in _names()}
    else:
        for n in _names():
            del sys.modules[n]
    kept = _LOADED.get(key)
    if kept is not None:
        sys.modules.update(kept)
    else:
        sys.path.insert(0, str(here))
        try:
            import run_idx  # noqa: F401
        finally:
            sys.path.remove(str(here))
        _LOADED[key] = {n: sys.modules[n] for n in _names()}
    _LIVE = key
    return _LOADED[key]["run_idx"]


def run_text(here, text):
    """Drive one program under a tree, returning its trace or a marker on failure."""
    try:
        mod = _swap(str(here), here)
        return mod.run(text)
    except Exception as exc:
        return ["!! %s: %s" % (type(exc).__name__, exc)]
