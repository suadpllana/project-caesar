"""Build an overlay tree outside the bundle and run a program through it.

Nothing here writes inside tasks/claim-cover-lift: an authoring run that leaves scratch in the
bundle ships it. Everything lands in a fresh tempfile.mkdtemp.
"""
import pathlib
import shutil
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
TASK = ROOT / "tasks" / "claim-cover-lift"
PARTS = ("hold.py", "fit.py", "line.py", "lift.py", "knot.py", "gate.py")

_TREES = {}


def tree(over=None):
    """A copy of the shipped app tree with `over` laid over /app/hb."""
    key = str(over)
    if key in _TREES:
        return _TREES[key]
    room = pathlib.Path(tempfile.mkdtemp(prefix="ccl-lab-"))
    here = room / "app"
    shutil.copytree(TASK / "environment" / "app_src", here)
    if over is not None:
        for part in PARTS:
            one = pathlib.Path(over) / part
            if one.is_file():
                shutil.copy(one, here / "hb" / part)
    _TREES[key] = here
    return here


_LOADED = None


def run(here, lines):
    """Run one program under one tree, in this process, and return its trace."""
    global _LOADED
    here = str(here)
    if _LOADED != here:
        for name in [n for n in sys.modules if n == "ops" or n == "hb" or n.startswith("hb.")]:
            del sys.modules[name]
        while here in sys.path:
            sys.path.remove(here)
        if _LOADED in sys.path:
            sys.path.remove(_LOADED)
        sys.path.insert(0, here)
        _LOADED = here
    import ops
    from hb import store
    st = store.Store()
    for raw in lines:
        raw = raw.strip()
        if raw:
            ops.ex(st, tuple(raw.split()))
    return st.out
