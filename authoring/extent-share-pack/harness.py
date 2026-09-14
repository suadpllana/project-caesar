"""Build a copy of the shipped tree with a chosen set of files laid over it, and run programs.

Every copy goes to a temp directory outside the bundle, so an authoring run can never be
packaged by mistake. Loading two trees in one process needs the `st` package dropped from
sys.modules between them, which `runner` does.
"""
import importlib
import pathlib
import shutil
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parent.parent / "tasks" / "extent-share-pack"
APP = TASK / "environment" / "app_src"
PARTS = ("ext.py", "pt.py", "pk.py", "step.py", "tot.py", "own.py")


def tree(over=None):
    """A fresh copy of the agent tree, with the .py files of `over` laid into st/."""
    room = pathlib.Path(tempfile.mkdtemp(prefix="esp-"))
    here = room / "app"
    shutil.copytree(APP, here)
    if over is not None:
        for part in PARTS:
            one = pathlib.Path(over) / part
            if one.is_file():
                shutil.copy(one, here / "st" / part)
    return here


def runner(over=None, root=None):
    """A callable taking a list of program lines and returning the printed trace."""
    here = pathlib.Path(root) if root else tree(over)

    def run(lines):
        for name in [m for m in sys.modules if m == "st" or m.startswith("st.") or m == "ops"]:
            del sys.modules[name]
        sys.path.insert(0, str(here))
        try:
            vol = importlib.import_module("st.vol")
            ops = importlib.import_module("ops")
            st = vol.Store()
            for line in lines:
                a = tuple(line.split())
                if a:
                    ops.ex(st, a)
            return list(st.out)
        finally:
            sys.path.remove(str(here))

    return run
